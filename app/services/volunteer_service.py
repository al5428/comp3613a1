from datetime import date

from sqlmodel import select

from app.repositories.volunteer_submission import (
    AdministratorRepository,
    AwardRepository,
    MilestoneRepository,
    RedeemedAwardRepository,
    StudentMilestoneRepository,
    StudentRepository,
    VolunteerSubmissionRepository,
)
from app.models.student_awards import Student, StudentMilestone
from app.models.user import User


class VolunteerService:
    def __init__(self, db):
        self.db = db
        self.administrator_repo = AdministratorRepository(db)
        self.repo = VolunteerSubmissionRepository(db)
        self.student_repo = StudentRepository(db)
        self.milestone_repo = MilestoneRepository(db)
        self.award_repo = AwardRepository(db)
        self.student_milestone_repo = StudentMilestoneRepository(db)
        self.redemption_repo = RedeemedAwardRepository(db)

    def _resolve_administrator_id(self, reviewer: User | None) -> int | None:
        if reviewer is None:
            return None
        return self.administrator_repo.get_or_create_for_user(reviewer).id

    def get_or_create_student_for_user(self, user):
        return self.student_repo.get_or_create_for_user(user)

    def get_or_create_student(self, student_id: int):
        student = self.student_repo.get_by_id(student_id)
        if student is not None:
            return student
        student = Student(
            user_id=student_id,
            name=f"Student {student_id}",
            email=f"student{student_id}@example.com",
            total_volunteer_hours=0,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def create_submission_for_user(
        self,
        user,
        *,
        activity_name: str,
        hours_worked: int,
        evidence: str,
        description: str = "",
        activity_date: date | None = None,
    ):
        student = self.get_or_create_student_for_user(user)
        return self.create_submission(
            student_id=student.id,
            activity_name=activity_name,
            hours_worked=hours_worked,
            evidence=evidence,
            description=description,
            activity_date=activity_date,
        )

    def create_submission(
        self,
        *,
        student_id: int,
        activity_name: str,
        hours_worked: int,
        evidence: str,
        description: str = "",
        activity_date: date | None = None,
    ):
        cleaned_name = (activity_name or "").strip()
        if not cleaned_name:
            raise ValueError("Activity name is required.")
        if hours_worked <= 0:
            raise ValueError("Hours worked must be greater than zero.")
        return self.repo.create(
            student_id=student_id,
            activity_name=cleaned_name,
            hours_worked=int(hours_worked),
            evidence=(evidence or "").strip(),
            description=(description or "").strip(),
            activity_date=activity_date,
        )

    def review_submission(self, submission_id: int, decision: str, *, reviewer: User | None = None, notes: str = ""):
        normalized = (decision or "").strip().lower()
        if normalized not in {"approved", "rejected"}:
            raise ValueError("Decision must be approved or rejected.")
        updated = self.repo.update_status(
            submission_id,
            status=normalized,
            administrator_id=self._resolve_administrator_id(reviewer),
            review_notes=notes,
        )
        self.sync_student_hours(updated.student_id)
        return updated

    def get_total_approved_hours(self, student_id: int) -> int:
        submissions = self.repo.list_approved_for_student(student_id)
        return sum(submission.hours_worked for submission in submissions)

    def sync_student_hours(self, student_id: int):
        student = self.get_or_create_student(student_id)
        total_approved = self.get_total_approved_hours(student_id)
        student.total_volunteer_hours = total_approved
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)

        milestones = self.milestone_repo.list_all()
        for milestone in milestones:
            if total_approved >= milestone.required_hours:
                self.student_milestone_repo.create_for_student(student_id, milestone.id)
        return student

    def list_milestones_for_student(self, student_id: int):
        student = self.sync_student_hours(student_id)
        total_approved = student.total_volunteer_hours
        award_names_by_milestone = {
            award.milestone_id: award.name for award in self.award_repo.list_all()
        }
        milestones = []
        for milestone in self.milestone_repo.list_all():
            unlocked = total_approved >= milestone.required_hours
            student_milestone = self.student_milestone_repo.get_for_student(student_id, milestone.id)
            progress = min(total_approved, milestone.required_hours)
            percent = 100 if milestone.required_hours == 0 else int((progress / milestone.required_hours) * 100)
            milestones.append(
                {
                    "id": milestone.id,
                    "name": milestone.name,
                    "award_name": award_names_by_milestone.get(milestone.id),
                    "required_hours": milestone.required_hours,
                    "description": milestone.description,
                    "progress": progress,
                    "progress_percent": min(100, percent),
                    "unlocked": unlocked,
                    "awarded_on": student_milestone.date_awarded if student_milestone else None,
                }
            )
        return milestones

    def list_awards_for_student(self, student_id: int):
        self.sync_student_hours(student_id)
        total_approved = self.get_total_approved_hours(student_id)
        awards = []
        for award in self.award_repo.list_all():
            milestone = self.milestone_repo.get_by_id(award.milestone_id)
            existing_redemption = self.redemption_repo.get_by_student_and_award(student_id, award.id)
            eligible = total_approved >= award.required_hours
            awards.append(
                {
                    "id": award.id,
                    "name": award.name,
                    "description": award.description,
                    "required_hours": award.required_hours,
                    "milestone_name": milestone.name if milestone else "General",
                    "eligible": eligible,
                    "redeemed": existing_redemption is not None,
                    "status": existing_redemption.status if existing_redemption else "not_requested",
                    "hours_remaining": max(0, award.required_hours - total_approved),
                }
            )
        return awards

    def redeem_award(self, student_id: int, award_id: int):
        student = self.sync_student_hours(student_id)
        award = self.award_repo.get_by_id(award_id)
        if award is None:
            raise ValueError("Award not found")
        if student.total_volunteer_hours < award.required_hours:
            raise ValueError("Student does not yet meet the hour requirement for this award.")
        existing = self.redemption_repo.get_by_student_and_award(student_id, award_id)
        if existing is not None:
            raise ValueError("This award has already been requested and cannot be redeemed again.")
        return self.redemption_repo.create(student_id=student_id, award_id=award_id)

    def list_pending_redemptions(self):
        items = self.redemption_repo.list_for_review()
        payload = []
        for item in items:
            award = self.award_repo.get_by_id(item.award_id)
            student = self.student_repo.get_by_id(item.student_id)
            payload.append({
                "id": item.id,
                "student_id": item.student_id,
                "student_name": student.name if student else "Unknown student",
                "award_name": award.name if award else "Unknown award",
                "award_required_hours": award.required_hours if award else 0,
                "status": item.status,
                "redemption_date": item.redemption_date,
            })
        return payload

    def review_redemption(self, redemption_id: int, decision: str, *, reviewer: User | None = None):
        normalized = (decision or "").strip().lower()
        if normalized not in {"approved", "rejected"}:
            raise ValueError("Decision must be approved or rejected.")
        return self.redemption_repo.update_status(
            redemption_id,
            status=normalized,
            administrator_id=self._resolve_administrator_id(reviewer),
        )

    def list_for_student(self, student_id: int):
        return self.repo.list_for_student(student_id)

    def list_for_review(self):
        return self.repo.list_for_review()

    def list_submissions_for_admin(self):
        # student-build:code-check service
        # Return the all-status administrator list through the repository.
        return self.repo.list_all_for_admin()

    def get_submission_detail_for_admin(self, submission_id: int):
        # student-build:code-check service
        # Return one submission together with its student's display name.
        submission = self.repo.get_by_id(submission_id)

        if submission is None:
            raise ValueError("Submission not found")

        student = self.student_repo.get_by_id(submission.student_id)

        return {
            "submission": submission,
            "student_name": student.name if student else "Unknown student",
        }

    def get_student_summary(self, student_id: int):
        self.sync_student_hours(student_id)
        submissions = self.list_for_student(student_id)
        approved = [s for s in submissions if s.status == "approved"]
        pending = [s for s in submissions if s.status == "pending"]
        total_approved = sum(s.hours_worked for s in approved)
        return {
            "total_approved": total_approved,
            "pending_count": len(pending),
            "submission_count": len(submissions),
        }