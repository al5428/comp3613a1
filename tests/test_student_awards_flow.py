from datetime import date

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine, select

from app.cli import (
    _ensure_submission_activity_date_column,
    _ensure_submission_description_column,
    _seed_demo_data,
)
from app.models.student_awards import (
    Administrator,
    Award,
    Milestone,
    RedeemedAward,
    Student,
    StudentMilestone,
    VolunteerSubmission,
)
from app.models.user import User
from app.services.volunteer_service import VolunteerService
from app.utilities.security import verify_password


def test_submit_and_review_flow():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = VolunteerService(session)

        submission = service.create_submission(
            student_id=1,
            activity_name="Beach clean-up",
            hours_worked=4,
            evidence="https://example.com/cleanup",
        )

        assert submission.status == "pending"
        assert submission.hours_worked == 4
        assert submission.activity_date is not None

        updated = service.review_submission(submission.id, "approved", reviewer_id=2)
        assert updated.status == "approved"
        assert updated.reviewer_id == 2


def test_student_service_resolves_user_to_different_student_id():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            id=13,
            username="bob",
            email="bob@gmail.com",
            password="hash",
            role="regular_user",
        )
        student = Student(
            id=11,
            user_id=13,
            name="Bob",
            email="bob@gmail.com",
            total_volunteer_hours=0,
        )
        session.add(user)
        session.add(student)
        session.commit()

        service = VolunteerService(session)
        resolved_student = service.get_or_create_student_for_user(user)
        submission = service.create_submission_for_user(
            user,
            activity_name="Food bank support",
            hours_worked=2,
            activity_date=date(2026, 10, 1),
            evidence="",
            description="Packed food parcels.",
        )

        assert user.id == 13
        assert resolved_student.id == 11
        assert submission.student_id == 11
        assert service.get_student_summary(resolved_student.id)["submission_count"] == 1


def test_milestone_unlock_and_award_redemption():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        service = VolunteerService(session)

        milestone = Milestone(name="Community Builder", required_hours=10, description="10 hours")
        session.add(milestone)
        session.commit()
        session.refresh(milestone)

        award = Award(name="Campus merch pack", description="For community leaders", required_hours=10, milestone_id=milestone.id)
        session.add(award)
        session.commit()
        session.refresh(award)

        submission = service.create_submission(
            student_id=1,
            activity_name="Neighborhood tutoring",
            hours_worked=10,
            evidence="https://example.com/tutoring",
        )
        service.review_submission(submission.id, "approved", reviewer_id=2)

        student = service.get_or_create_student(student_id=1)
        service.sync_student_hours(student.id)
        milestones = service.list_milestones_for_student(student.id)
        community_milestone = next(item for item in milestones if item["name"] == "Community Builder")
        assert community_milestone["unlocked"]
        assert community_milestone["award_name"] == "Campus merch pack"
        assert community_milestone["required_hours"] == 10
        assert community_milestone["progress"] == 10

        redemption = service.redeem_award(student.id, award.id)
        assert redemption.status == "pending"
        assert redemption.student_id == student.id

        service.review_redemption(redemption.id, "rejected", reviewer_id=2)
        award_state = next(item for item in service.list_awards_for_student(student.id) if item["id"] == award.id)
        assert award_state["redeemed"]
        assert award_state["status"] == "rejected"
        try:
            service.redeem_award(student.id, award.id)
        except ValueError:
            pass
        else:
            raise AssertionError("A rejected award must not be redeemed a second time")


def test_demo_seed_data_is_consistent_and_rerunnable():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        created, skipped = _seed_demo_data(session)
        assert created == 13
        assert skipped == 0

        users = session.exec(select(User)).all()
        students = session.exec(select(Student)).all()
        administrators = session.exec(select(Administrator)).all()
        submissions = session.exec(select(VolunteerSubmission)).all()
        milestones = session.exec(select(Milestone)).all()
        awards = session.exec(select(Award)).all()
        redemptions = session.exec(select(RedeemedAward)).all()

        assert len(users) == 13
        assert sum(user.role == "regular_user" for user in users) == 11
        assert sum(user.role == "admin" for user in users) == 2
        assert len(students) == 11
        assert len(administrators) == 2
        assert len(submissions) == 30
        user_by_id = {user.id: user for user in users}
        student_names_by_username = {
            user_by_id[student.user_id].username: student.name for student in students
        }
        assert {
            "Bruce Wayne": "Bruce Wayne",
            "Vert Wheeler": "Vert Wheeler",
            "Kyryll Flins": "Kyryll Flins",
            "Fang Runin": "Fang Runin",
            "Percy Jackson": "Percy Jackson",
            "Evie Sage": "Evie Sage",
            "Jake Peralta": "Jake Peralta",
            "Mitchell Pritchett": "Mitchell Pritchett",
            "Rick Sanchez": "Rick Sanchez",
            "John Stewart": "John Stewart",
            "bob": "Bob",
        } == student_names_by_username
        student_user_ids = {student.user_id for student in students}
        assert all(
            verify_password(
                "bobpass" if user_by_id[user_id].username == "bob" else "studentpass",
                user_by_id[user_id].password,
            )
            for user_id in student_user_ids
        )
        assert all(
            user_by_id[student.user_id].email
            == f"{student.name.lower().replace(' ', '.')}@gmail.com"
            for student in students
        )
        bob_user = next(user for user in users if user.username == "bob")
        bob_student = next(student for student in students if student.user_id == bob_user.id)
        bob_summary = VolunteerService(session).get_student_summary(bob_student.id)
        assert bob_summary["submission_count"] == 0
        review_items = VolunteerService(session).list_for_review()
        admin_submissions = VolunteerService(session).list_submissions_for_admin()
        student_by_id = {student.id: student for student in students}
        assert review_items
        assert len(admin_submissions) == len(submissions)
        assert {submission.status for submission, _ in admin_submissions} == {
            "pending",
            "approved",
            "rejected",
        }
        assert all(
            student_name == student_by_id[submission.student_id].name
            for submission, student_name in admin_submissions
        )
        detail = VolunteerService(session).get_submission_detail_for_admin(
            admin_submissions[0][0].id
        )
        assert detail["submission"].id == admin_submissions[0][0].id
        assert detail["student_name"] == student_by_id[detail["submission"].student_id].name
        assert all(
            submission.student_id in student_by_id
            and student_name == student_by_id[submission.student_id].name
            for submission, student_name in review_items
        )
        pending_redemptions = VolunteerService(session).list_pending_redemptions()
        assert pending_redemptions
        assert all(
            item["student_id"] in student_by_id
            and item["student_name"] == student_by_id[item["student_id"]].name
            for item in pending_redemptions
        )
        assert {submission.status for submission in submissions} == {"pending", "approved", "rejected"}
        assert all(submission.description and submission.submission_date for submission in submissions)
        seeded_submissions = {submission.activity_name: submission for submission in submissions}
        rejected_example = seeded_submissions["Library book sale"]
        assert rejected_example.description == "Sorted donated books and organized them for the campus sale."
        assert rejected_example.review_notes == "Attendance confirmation was not provided."
        assert {milestone.required_hours for milestone in milestones} == {25, 50, 100}
        assert {award.name for award in awards} == {"Plaque", "Medal", "Trophy"}

        milestone_by_id = {milestone.id: milestone for milestone in milestones}
        award_by_id = {award.id: award for award in awards}
        submissions_by_student = {}
        for submission in submissions:
            submissions_by_student.setdefault(submission.student_id, []).append(submission)
        milestone_pairs = {
            (record.student_id, milestone_by_id[record.milestone_id].required_hours)
            for record in session.exec(select(StudentMilestone)).all()
        }
        expected_milestone_pairs = set()
        for student in students:
            approved_hours = sum(
                submission.hours_worked
                    for submission in submissions_by_student.get(student.id, [])
                if submission.status == "approved"
            )
            assert student.total_volunteer_hours == approved_hours
            expected_milestone_pairs.update(
                (student.id, required_hours)
                for required_hours in (25, 50, 100)
                if approved_hours >= required_hours
            )
        assert milestone_pairs == expected_milestone_pairs
        assert any(student.total_volunteer_hours == 0 for student in students)
        assert any(hours >= 100 for _, hours in milestone_pairs)
        assert {redemption.status for redemption in redemptions} == {"pending", "approved", "rejected"}
        assert all(
            next(student for student in students if student.id == redemption.student_id).total_volunteer_hours
            >= award_by_id[redemption.award_id].required_hours
            for redemption in redemptions
        )

        legacy_usernames = {
            "Vert Wheeler": "student01",
            "Kyryll Flins": "student02",
            "Fang Runin": "student03",
            "Percy Jackson": "student04",
            "Evie Sage": "student05",
            "Jake Peralta": "student06",
            "Mitchell Pritchett": "student07",
            "Rick Sanchez": "student08",
            "John Stewart": "student09",
        }
        student_user_ids = {student.user_id for student in students}
        for student in students:
            user = user_by_id[student.user_id]
            if student.name in legacy_usernames:
                user.username = legacy_usernames[student.name]
            user.password = "stale-password-hash"
            session.add(user)
        session.commit()

        _seed_demo_data(session)
        assert len(session.exec(select(VolunteerSubmission)).all()) == 30
        assert len(session.exec(select(RedeemedAward)).all()) == 6
        migrated_users = session.exec(select(User)).all()
        assert all(
            verify_password("bobpass" if user.username == "bob" else "studentpass", user.password)
            for user in migrated_users
            if user.id in student_user_ids
        )
        assert all(
            (
                next(student for student in students if student.user_id == user.id).name == user.username
                if user.username != "bob"
                else next(student for student in students if student.user_id == user.id).name == "Bob"
            )
            for user in migrated_users
            if user.id in student_user_ids
        )


def test_legacy_bob_account_is_migrated_without_losing_student_history():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        legacy_user = User(
            username="bob",
            email="bob@example.com",
            password="legacy-password-hash",
            role="regular_user",
        )
        session.add(legacy_user)
        session.commit()
        session.refresh(legacy_user)
        legacy_student = Student(
            user_id=legacy_user.id,
            name="Bruce Wayne",
            email="bob@example.com",
            total_volunteer_hours=0,
        )
        session.add(legacy_student)
        session.commit()
        legacy_user_id = legacy_user.id
        legacy_student_id = legacy_student.id

        _seed_demo_data(session)

        migrated_bruce = session.exec(
            select(User).where(User.username == "Bruce Wayne")
        ).one()
        bob = session.exec(select(User).where(User.username == "bob")).one()
        bruce_student = session.exec(
            select(Student).where(Student.user_id == migrated_bruce.id)
        ).one()
        bob_student = session.exec(select(Student).where(Student.user_id == bob.id)).one()
        assert migrated_bruce.id == legacy_user_id
        assert bruce_student.id == legacy_student_id
        assert bruce_student.name == "Bruce Wayne"
        assert bob_student.name == "Bob"
        assert verify_password("studentpass", migrated_bruce.password)
        assert verify_password("bobpass", bob.password)


def test_seed_adds_description_column_to_legacy_submission_table():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE volunteersubmission (id INTEGER PRIMARY KEY)"))

    _ensure_submission_description_column(engine)

    column_names = {column["name"] for column in inspect(engine).get_columns("volunteersubmission")}
    assert "description" in column_names


def test_seed_adds_and_backfills_activity_date_column():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE volunteersubmission (id INTEGER PRIMARY KEY, submission_date TEXT)"
        ))
        connection.execute(text(
            "INSERT INTO volunteersubmission (id, submission_date) VALUES (1, '2026-09-15 12:30:00')"
        ))

    _ensure_submission_activity_date_column(engine)

    column_names = {column["name"] for column in inspect(engine).get_columns("volunteersubmission")}
    with engine.connect() as connection:
        activity_date = connection.execute(
            text("SELECT activity_date FROM volunteersubmission WHERE id = 1")
        ).scalar_one()
    assert "activity_date" in column_names
    assert str(activity_date) == "2026-09-15"
