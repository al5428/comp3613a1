from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.models.student_awards import (
    Administrator,
    Award,
    Milestone,
    RedeemedAward,
    Student,
    StudentMilestone,
    VolunteerSubmission,
)


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, student_id: int) -> Student | None:
        return self.db.get(Student, student_id)

    def get_by_user_id(self, user_id: int) -> Student | None:
        return self.db.exec(select(Student).where(Student.user_id == user_id)).one_or_none()

    def get_or_create_for_user(self, user) -> Student:
        existing = self.get_by_user_id(user.id)
        if existing is not None:
            return existing
        entity = Student(
            user_id=user.id,
            name=user.username,
            email=user.email,
            total_volunteer_hours=0,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update_total_hours(self, student_id: int, total_hours: int) -> Student:
        student = self.get_by_id(student_id)
        if student is None:
            raise ValueError("Student not found")
        student.total_volunteer_hours = total_hours
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student


class AdministratorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Administrator | None:
        return self.db.exec(select(Administrator).where(Administrator.user_id == user_id)).one_or_none()

    def get_or_create_for_user(self, user) -> Administrator:
        existing = self.get_by_user_id(user.id)
        if existing is not None:
            return existing
        entity = Administrator(
            user_id=user.id,
            name=user.username,
            email=user.email,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity


class MilestoneRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self):
        return self.db.exec(select(Milestone).order_by(Milestone.required_hours.asc())).all()

    def get_by_id(self, milestone_id: int) -> Milestone | None:
        return self.db.get(Milestone, milestone_id)


class AwardRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self):
        return self.db.exec(select(Award).order_by(Award.required_hours.asc())).all()

    def get_by_id(self, award_id: int) -> Award | None:
        return self.db.get(Award, award_id)


class StudentMilestoneRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_student(self, student_id: int, milestone_id: int) -> StudentMilestone | None:
        statement = select(StudentMilestone).where(
            StudentMilestone.student_id == student_id,
            StudentMilestone.milestone_id == milestone_id,
        )
        return self.db.exec(statement).one_or_none()

    def create_for_student(self, student_id: int, milestone_id: int) -> StudentMilestone:
        existing = self.get_for_student(student_id, milestone_id)
        if existing is not None:
            return existing
        item = StudentMilestone(student_id=student_id, milestone_id=milestone_id)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item


class RedeemedAwardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, redemption_id: int) -> RedeemedAward | None:
        return self.db.get(RedeemedAward, redemption_id)

    def get_by_student_and_award(self, student_id: int, award_id: int) -> RedeemedAward | None:
        statement = select(RedeemedAward).where(
            RedeemedAward.student_id == student_id,
            RedeemedAward.award_id == award_id,
        )
        statement = statement.order_by(RedeemedAward.redemption_date.desc())
        return self.db.exec(statement).first()

    def list_for_student(self, student_id: int):
        statement = select(RedeemedAward).where(RedeemedAward.student_id == student_id)
        statement = statement.order_by(RedeemedAward.redemption_date.desc())
        return self.db.exec(statement).all()

    def list_for_review(self):
        statement = select(RedeemedAward).where(RedeemedAward.status.in_({"pending", "processing"}))
        statement = statement.order_by(RedeemedAward.redemption_date.asc())
        return self.db.exec(statement).all()

    def create(self, *, student_id: int, award_id: int) -> RedeemedAward:
        item = RedeemedAward(student_id=student_id, award_id=award_id, status="pending")
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_status(self, redemption_id: int, *, status: str, administrator_id: int | None = None) -> RedeemedAward:
        redemption = self.get_by_id(redemption_id)
        if redemption is None:
            raise ValueError("Award redemption not found")
        redemption.status = status
        redemption.administrator_id = administrator_id
        self.db.add(redemption)
        self.db.commit()
        self.db.refresh(redemption)
        return redemption


class VolunteerSubmissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        student_id: int,
        activity_name: str,
        hours_worked: int,
        evidence: str,
        description: str = "",
        activity_date: date | None = None,
    ) -> VolunteerSubmission:
        submission = VolunteerSubmission(
            student_id=student_id,
            activity_date=activity_date or date.today(),
            activity_name=activity_name.strip(),
            description=description.strip(),
            hours_worked=hours_worked,
            evidence=evidence.strip(),
            status="pending",
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def get_by_id(self, submission_id: int) -> VolunteerSubmission | None:
        return self.db.get(VolunteerSubmission, submission_id)

    def list_for_student(self, student_id: int):
        statement = select(VolunteerSubmission).where(VolunteerSubmission.student_id == student_id)
        statement = statement.order_by(VolunteerSubmission.submission_date.desc())
        return self.db.exec(statement).all()

    def list_for_review(self):
        statement = (
            select(VolunteerSubmission, Student.name)
            .outerjoin(Student, Student.id == VolunteerSubmission.student_id)
            .where(VolunteerSubmission.status == "pending")
        )
        statement = statement.order_by(VolunteerSubmission.submission_date.asc())
        return self.db.exec(statement).all()

    def list_all_for_admin(self):
        # student-build:code-check repository
        # Return all submissions with student names, newest first.
        statement = (
            select(VolunteerSubmission, Student.name)
            .outerjoin(Student, Student.id == VolunteerSubmission.student_id)
        )
        statement = statement.order_by(VolunteerSubmission.submission_date.desc())
        return self.db.exec(statement).all()

    def list_approved_for_student(self, student_id: int):
        statement = select(VolunteerSubmission).where(
            VolunteerSubmission.student_id == student_id,
            VolunteerSubmission.status == "approved",
        )
        return self.db.exec(statement).all()

    def update_status(self, submission_id: int, *, status: str, administrator_id: int | None = None, review_notes: str = "") -> VolunteerSubmission:
        submission = self.get_by_id(submission_id)
        if submission is None:
            raise ValueError("Submission not found")

        submission.status = status
        submission.administrator_id = administrator_id
        submission.review_notes = review_notes.strip()
        submission.reviewed_at = datetime.now(timezone.utc)
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission
