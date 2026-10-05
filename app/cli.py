#!/usr/bin/env python3
"""FastStarter project CLI — stdlib argparse (no extra CLI library).

From the project root (venv active, deps installed; ``.env`` optional — falls back to ``.env.example``):

    python manage.py init
    python manage.py run
    python manage.py users
    python manage.py report --name "Student Name" --id "816000000"
    python manage.py usecase
    python manage.py skills-verify
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_models_loaded() -> None:
    import app.models  # noqa: F401


def cmd_init(args: argparse.Namespace) -> None:
    """Create database tables (drops existing by default) and seed demo users."""
    from app.config import get_settings
    from app.database import drop_all, ensure_db_and_tables

    _ensure_models_loaded()
    if args.drop:
        print("Dropping all tables…")
        # Drop can fail on a brand-new empty DB; create path still retries.
        try:
            drop_all()
        except Exception as exc:  # noqa: BLE001
            from app.database import is_db_not_ready_error

            if not is_db_not_ready_error(exc):
                raise
            print(f"Database not ready yet while dropping ({exc}); continuing…")
    print("Creating tables…")
    ensure_db_and_tables()
    print(f"Database ready ({get_settings().database_uri}).")
    if getattr(args, "seed", True):
        cmd_seed(args)


def _ensure_submission_description_column(engine) -> None:
    from sqlalchemy import inspect, text

    columns = {column["name"] for column in inspect(engine).get_columns("volunteersubmission")}
    if "description" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE volunteersubmission ADD COLUMN description VARCHAR NOT NULL DEFAULT ''")
            )


def _ensure_submission_activity_date_column(engine) -> None:
    from datetime import date

    from sqlalchemy import inspect, text

    columns = {column["name"] for column in inspect(engine).get_columns("volunteersubmission")}
    if "activity_date" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE volunteersubmission ADD COLUMN activity_date DATE"))

    with engine.begin() as connection:
        legacy_rows = connection.execute(
            text("SELECT id, submission_date FROM volunteersubmission WHERE activity_date IS NULL")
        ).all()
        for row in legacy_rows:
            activity_date = date.fromisoformat(str(row.submission_date)[:10]) if row.submission_date else date.today()
            connection.execute(
                text("UPDATE volunteersubmission SET activity_date = :activity_date WHERE id = :submission_id"),
                {"activity_date": activity_date, "submission_id": row.id},
            )


def _seed_demo_data(session) -> tuple[int, int]:
    from datetime import datetime, timedelta, timezone

    from sqlmodel import select

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
    from app.repositories.user import UserRepository
    from app.repositories.volunteer_submission import AdministratorRepository, StudentRepository
    from app.schemas.user import AdminCreate, RegularUserCreate
    from app.utilities.security import encrypt_password

    student_specs = [
        ("bob", "bruce.wayne@gmail.com", "Bruce Wayne", 24),
        ("student01", "vert.wheeler@gmail.com", "Vert Wheeler", 0),
        ("student02", "kyryll.flins@gmail.com", "Kyryll Flins", 18),
        ("student03", "fang.runin@gmail.com", "Fang Runin", 30),
        ("student04", "percy.jackson@gmail.com", "Percy Jackson", 45),
        ("student05", "evie.sage@gmail.com", "Evie Sage", 55),
        ("student06", "jake.peralta@gmail.com", "Jake Peralta", 72),
        ("student07", "mitchell.pritchett@gmail.com", "Mitchell Pritchett", 100),
        ("student08", "rick.sanchez@gmail.com", "Rick Sanchez", 110),
        ("student09", "john.stewart@gmail.com", "John Stewart", 40),
    ]
    admin_specs = [
        ("admin", "admin@example.com", "adminpass"),
        ("admin2", "admin2@example.com", "adminpass"),
    ]
    demo_users = [
        *((name, email, "studentpass", "regular_user")
          for _, email, name, _ in student_specs),
        ("bob", "bob@gmail.com", "bobpass", "regular_user"),
        *((username, email, password, "admin") for username, email, password in admin_specs),
    ]

    user_repo = UserRepository(session)
    legacy_bob = user_repo.get_by_username("bob")
    if legacy_bob is not None and legacy_bob.email == "bob@example.com":
        legacy_bob_student = session.exec(
            select(Student).where(Student.user_id == legacy_bob.id)
        ).one_or_none()
        if (
            legacy_bob_student is not None
            and legacy_bob_student.name == "Bruce Wayne"
            and user_repo.get_by_username("Bruce Wayne") is None
        ):
            legacy_bob.username = "Bruce Wayne"
            legacy_bob.email = "bruce.wayne@gmail.com"
            legacy_bob.password = encrypt_password("studentpass")
            session.add(legacy_bob)
            session.commit()

    created = 0
    skipped = 0
    for username, email, password, role in demo_users:
        user = user_repo.get_by_username(username)
        if user is None and role == "regular_user":
            user = session.exec(select(User).where(User.email == email)).one_or_none()
        if user is not None:
            skipped += 1
            if role == "regular_user":
                user.username = username
                user.email = email
                user.password = encrypt_password(password)
                user.role = role
                session.add(user)
                session.commit()
            continue
        payload_cls = AdminCreate if role == "admin" else RegularUserCreate
        user_repo.create(
            payload_cls(
                username=username,
                email=email,
                password=encrypt_password(password),
                role=role,
            )
        )
        created += 1

    student_repo = StudentRepository(session)
    students = {}
    for account_key, email, name, _ in student_specs:
        user = session.exec(select(User).where(User.email == email)).one()
        student = student_repo.get_or_create_for_user(user)
        student.name = name
        student.email = email
        session.add(student)
        students[account_key] = student

    bob_user = user_repo.get_by_username("bob")
    bob_student = student_repo.get_or_create_for_user(bob_user)
    bob_student.name = "Bob"
    bob_student.email = "bob@gmail.com"
    bob_student.total_volunteer_hours = 0
    session.add(bob_student)
    students["bob_account"] = bob_student

    admin_repo = AdministratorRepository(session)
    administrators = {}
    for username, email, _ in admin_specs:
        user = user_repo.get_by_username(username)
        administrator = admin_repo.get_or_create_for_user(user)
        administrator.name = "Alex Morgan" if username == "admin" else "Jordan Lee"
        administrator.email = email
        session.add(administrator)
        administrators[username] = administrator
    session.commit()

    milestone_specs = [
        ("Tier 1", 25, 'Reach 25 approved volunteer hours to unlock the "Plaque Milestone".'),
        ("Tier 2", 50, 'Reach 50 approved volunteer hours to unlock the "Medal Milestone".'),
        ("Tier 3", 100, 'Reach 100 approved volunteer hours to unlock the "Trophy Milestone".'),
    ]
    milestones = {item.name: item for item in session.exec(select(Milestone)).all()}
    legacy_milestone_names = {"Tier 1": "Starter Service", "Tier 2": "Community Builder"}
    for name, required_hours, description in milestone_specs:
        milestone = milestones.get(name) or milestones.get(legacy_milestone_names.get(name, ""))
        if milestone is None:
            milestone = Milestone(name=name)
        milestone.name = name
        milestone.required_hours = required_hours
        milestone.description = description
        session.add(milestone)
        milestones[name] = milestone
    session.commit()
    for milestone in milestones.values():
        session.refresh(milestone)

    award_specs = [
        ("Plaque", "A commemorative plaque for 25 approved volunteer hours.", 25, "Tier 1"),
        ("Medal", "A service medal for 50 approved volunteer hours.", 50, "Tier 2"),
        ("Trophy", "A community service trophy for 100 approved volunteer hours.", 100, "Tier 3"),
    ]
    awards = {item.name: item for item in session.exec(select(Award)).all()}
    legacy_award_names = {"Plaque": "Campus tote bag", "Medal": "Campus merch pack"}
    for name, description, required_hours, milestone_name in award_specs:
        award = awards.get(name) or awards.get(legacy_award_names.get(name, ""))
        if award is None:
            award = Award(name=name)
        award.name = name
        award.description = description
        award.required_hours = required_hours
        award.milestone_id = milestones[milestone_name].id
        session.add(award)
        awards[name] = award
    session.commit()
    for award in awards.values():
        session.refresh(award)

    submission_specs = {
        "bob": [
            ("Food pantry sorting", 14, "approved", 90, "Sorted and packed weekly grocery parcels for local families.", True),
            ("Reading buddy program", 10, "approved", 35, "Read with primary students and helped them practice fluency.", True),
            ("Community garden cleanup", 3, "pending", 8, "Cleared planting beds and prepared compost for the next volunteer day.", True),
        ],
        "student01": [
            ("Donation drive setup", 4, "rejected", 28, "Helped arrange collection bins before the campus drive.", False),
            ("Park litter pickup", 2, "pending", 7, "Collected litter along the eastern walking path.", True),
            ("Library book sale", 3, "rejected", 3, "Sorted donated books and organized them for the campus sale.", False),
        ],
        "student02": [
            ("Senior center technology help", 10, "approved", 78, "Helped residents use email and video calling.", True),
            ("After-school math club", 8, "approved", 32, "Supported students with weekly math practice.", True),
            ("Neighborhood pantry delivery", 3, "pending", 6, "Delivered pantry boxes to residents who could not travel.", True),
        ],
        "student03": [
            ("Coastal cleanup", 16, "approved", 84, "Collected waste and logged the cleanup area with the team lead.", True),
            ("School reading circle", 14, "approved", 38, "Led a small-group reading session for grade-six students.", True),
            ("Campus welcome team", 4, "pending", 5, "Answered new students' questions during orientation.", True),
        ],
        "student04": [
            ("Food bank inventory", 25, "approved", 82, "Counted incoming donations and organized pantry shelves.", True),
            ("Adaptive sports day", 20, "approved", 36, "Assisted participants and prepared accessible activity stations.", True),
            ("Tree planting morning", 2, "pending", 4, "Planted native seedlings with the neighborhood group.", True),
        ],
        "student05": [
            ("Community health fair", 30, "approved", 76, "Supported registration and directed visitors to health services.", True),
            ("Youth arts workshop", 25, "approved", 34, "Prepared materials and mentored students during the workshop.", True),
            ("Shelter meal service", 3, "rejected", 2, "Served meals and helped clean the dining area at the shelter.", False),
        ],
        "student06": [
            ("Watershed restoration", 38, "approved", 72, "Removed invasive plants and helped restore the riverbank.", True),
            ("Homework support sessions", 34, "approved", 30, "Provided weekly homework support at the youth center.", True),
            ("Clothing closet sorting", 2, "rejected", 1, "Sorted clothing donations by type and size for the community closet.", False),
        ],
        "student07": [
            ("Accessible trail project", 50, "approved", 68, "Improved trail access and documented completed work sections.", True),
            ("Community language exchange", 50, "approved", 26, "Helped newcomers practice conversational English.", True),
            ("Winter supply collection", 4, "rejected", 1, "Collected and organized winter supplies for the community drive.", False),
        ],
        "student08": [
            ("Disaster relief packing", 60, "approved", 64, "Packed hygiene and first-aid kits for the regional relief drive.", True),
            ("Meals on Wheels route", 50, "approved", 24, "Prepared and delivered meals with an approved volunteer driver.", True),
            ("Campus peer mentoring", 3, "rejected", 1, "Helped new students find campus services and get oriented.", False),
        ],
        "student09": [
            ("Animal shelter support", 22, "approved", 58, "Prepared enrichment activities and assisted with adoption events.", True),
            ("Neighborhood tutoring", 18, "approved", 22, "Tutored middle-school students in science and reading.", True),
            ("Festival recycling team", 2, "rejected", 1, "Sorted recyclable materials and maintained collection stations during the festival.", False),
        ],
    }
    seed_time = datetime.now(timezone.utc)
    review_note_overrides = {
        "Library book sale": "Attendance confirmation was not provided.",
        "Shelter meal service": "Supervisor confirmation was not provided.",
        "Clothing closet sorting": "The evidence did not verify volunteer participation.",
        "Winter supply collection": "This entry duplicated hours from another submission.",
        "Campus peer mentoring": "The activity date did not match the attached sign-in sheet.",
        "Festival recycling team": "The evidence link was unavailable during review.",
    }
    legacy_bob_names = {"Library reading mentor", "Campus food drive"}
    legacy_bob_rows = session.exec(
        select(VolunteerSubmission).where(
            VolunteerSubmission.student_id == students["bob"].id,
            VolunteerSubmission.activity_name.in_(legacy_bob_names),
        )
    ).all()
    for username, records in submission_specs.items():
        student = students[username]
        for index, (activity, hours, status, days_ago, description, has_evidence) in enumerate(records):
            submission = session.exec(
                select(VolunteerSubmission).where(
                    VolunteerSubmission.student_id == student.id,
                    VolunteerSubmission.activity_name == activity,
                )
            ).one_or_none()
            if submission is None and username == "bob" and legacy_bob_rows:
                submission = legacy_bob_rows.pop(0)
            if submission is None:
                submission = VolunteerSubmission(student_id=student.id, activity_name=activity)
            submission.student_id = student.id
            submission.activity_name = activity
            submission.description = description
            submission.hours_worked = hours
            submission.submission_date = seed_time - timedelta(days=days_ago)
            submission.activity_date = submission.submission_date.date()
            submission.status = status
            submission.evidence = (
                f"https://example.org/volunteer-evidence/{username}/{index + 1}" if has_evidence else ""
            )
            submission.administrator_id = None
            submission.review_notes = ""
            submission.reviewed_at = None
            if status != "pending":
                reviewer_name = "admin" if index % 2 == 0 else "admin2"
                submission.administrator_id = administrators[reviewer_name].id
                submission.reviewed_at = submission.submission_date + timedelta(days=2)
                submission.review_notes = (
                    "Hours and supporting evidence verified."
                    if status == "approved"
                    else review_note_overrides.get(
                        activity,
                        "The submission could not be verified during review.",
                    )
                )
            session.add(submission)
    session.commit()

    milestones_by_hours = {milestone.required_hours: milestone for milestone in milestones.values()}
    for student in students.values():
        submissions = session.exec(
            select(VolunteerSubmission).where(VolunteerSubmission.student_id == student.id)
        ).all()
        approved = sorted(
            (item for item in submissions if item.status == "approved"),
            key=lambda item: item.submission_date,
        )
        student.total_volunteer_hours = sum(item.hours_worked for item in approved)
        session.add(student)

        earned_on = {}
        running_total = 0
        for submission in approved:
            running_total += submission.hours_worked
            for required_hours, milestone in milestones_by_hours.items():
                if running_total >= required_hours and milestone.id not in earned_on:
                    earned_on[milestone.id] = submission.submission_date

        existing_records = session.exec(
            select(StudentMilestone).where(StudentMilestone.student_id == student.id)
        ).all()
        existing_by_milestone = {record.milestone_id: record for record in existing_records}
        for milestone in milestones_by_hours.values():
            record = existing_by_milestone.get(milestone.id)
            if milestone.id not in earned_on:
                if record is not None:
                    session.delete(record)
                continue
            if record is None:
                record = StudentMilestone(student_id=student.id, milestone_id=milestone.id)
            record.date_awarded = earned_on[milestone.id]
            session.add(record)
    session.commit()

    redemption_specs = [
        ("student03", "Plaque", "pending", 18, "admin"),
        ("student05", "Plaque", "approved", 14, "admin2"),
        ("student06", "Medal", "pending", 12, "admin"),
        ("student07", "Trophy", "approved", 10, "admin2"),
        ("student08", "Trophy", "rejected", 8, "admin"),
        ("student09", "Plaque", "rejected", 6, "admin2"),
    ]
    for username, award_name, status, days_ago, administrator_name in redemption_specs:
        student = students[username]
        award = awards[award_name]
        if student.total_volunteer_hours < award.required_hours:
            raise ValueError(f"Seed redemption is ineligible: {username} / {award_name}")
        redemption = session.exec(
            select(RedeemedAward).where(
                RedeemedAward.student_id == student.id,
                RedeemedAward.award_id == award.id,
            )
        ).first()
        if redemption is None:
            redemption = RedeemedAward(student_id=student.id, award_id=award.id)
        redemption.status = status
        redemption.redemption_date = seed_time - timedelta(days=days_ago)
        redemption.administrator_id = (
            None if status in {"pending", "processing"} else administrators[administrator_name].id
        )
        session.add(redemption)
    session.commit()
    return created, skipped


def cmd_seed(args: argparse.Namespace) -> None:
    """Seed demo accounts and realistic Student Awards workflow data."""
    from app.database import engine, ensure_db_and_tables, get_cli_session

    _ensure_models_loaded()
    ensure_db_and_tables()
    _ensure_submission_description_column(engine)
    _ensure_submission_activity_date_column(engine)

    with get_cli_session() as session:
        created, skipped = _seed_demo_data(session)

    print(f"Seed done — created {created}, skipped {skipped}.")
    print("Student logins: full-name usernames/studentpass and bob/bobpass")
    print("Administrator logins: admin/adminpass and admin2/adminpass")


def cmd_run(args: argparse.Namespace) -> None:
    """Start the FastAPI app with Uvicorn."""
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    bind_host = args.host or settings.app_host
    bind_port = args.port or settings.app_port
    if args.reload is None:
        use_reload = settings.env.lower() != "production"
    else:
        use_reload = args.reload
    print(f"Starting FastStarter on http://{bind_host}:{bind_port} (reload={use_reload})")
    uvicorn.run(
        "app.main:app",
        host=bind_host,
        port=bind_port,
        reload=use_reload,
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Build the submission package: merge judge, package transcripts, write PDF.

    Guide must (1) write ``docs/judge.md`` and (2) pull every Guide chat into
    ``docs/transcripts/*.md`` before this command. Report only packages those files.
    """
    from app.report_pdf import export_report
    from app.skill_integrity import format_report, verify

    result = export_report(
        name=args.name,
        student_id=args.student_id,
        source=None if args.src is None else Path(args.src),
        output=None if args.output is None else Path(args.output),
    )
    print()
    print("Report package:")
    print(
        f"  Judge:       {'merged docs/judge.md' if result.judge_merged else 'MISSING - Guide must run student-judge first'}"
    )
    print(
        f"  Transcripts: {result.transcript_count} chat(s) in docs/transcripts/"
        + (
            ""
            if result.transcript_count
            else " (EMPTY - Guide must pull Copilot/Cursor/OpenCode chats first)"
        )
    )
    if result.transcript_zip:
        print(f"  Zip:         {result.transcript_zip.as_posix()}")
    print(f"  PDF:         {result.pdf_path.as_posix()}")
    print(format_report(verify()))


def cmd_transcripts(args: argparse.Namespace) -> None:
    """Package agent-written markdown under docs/transcripts/ (+ zip)."""
    from app.transcript_export import package_transcripts

    result = package_transcripts(make_zip=not args.no_zip)
    if result.found == 0:
        print(
            "Warning: no chat markdown in docs/transcripts/. "
            "The Guide agent must pull every Guide chat for this project "
            "(Copilot Agent, Cursor, or OpenCode) into docs/transcripts/<slug>.md first."
        )
        raise SystemExit(2)
    print(f"Submission package ready: {result.out_dir}")
    if result.zip_path:
        print(f"Zip for submission: {result.zip_path}")


def cmd_skills_verify(args: argparse.Namespace) -> None:
    """Check course skill files against .agents/skills.lock.json."""
    from app.skill_integrity import format_report, verify

    result = verify()
    print(format_report(result))
    if not result.ok:
        raise SystemExit(1)


def cmd_usecase(args: argparse.Namespace) -> None:
    """Render docs/diagrams/use-case.json to a UML use-case PNG."""
    from app.usecase_diagram import render_usecase_png

    dest = render_usecase_png(
        spec_path=None if args.spec is None else Path(args.spec),
        output=None if args.output is None else Path(args.output),
    )
    print(f"Wrote {dest}")


def cmd_skills_lock(args: argparse.Namespace) -> None:
    """Rewrite the skill lockfile (course authors only)."""
    from app.skill_integrity import write_lock

    dest = write_lock()
    print(f"Wrote {dest}")


def cmd_users(args: argparse.Namespace) -> None:
    """List users currently in the database."""
    from sqlmodel import select

    from app.database import get_cli_session
    from app.models.user import User

    _ensure_models_loaded()
    with get_cli_session() as session:
        users = session.exec(select(User)).all()
        if not users:
            print("No users found. Run: python manage.py init")
            return
        for user in users:
            print(
                f"  id={user.id}  username={user.username}  "
                f"role={user.role}  email={user.email}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="FastStarter Python CLI — init database, seed demo data, run the app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create DB tables and seed demo users (drops existing tables by default)",
    )
    p_init.add_argument(
        "--no-drop",
        dest="drop",
        action="store_false",
        help="Create tables without dropping existing ones",
    )
    p_init.add_argument(
        "--no-seed",
        dest="seed",
        action="store_false",
        help="Skip demo user seed after creating tables",
    )
    p_init.set_defaults(drop=True, seed=True, func=cmd_init)

    p_seed = sub.add_parser(
        "seed",
        help="Insert demo users only (idempotent; also runs as part of init)",
    )
    p_seed.set_defaults(func=cmd_seed)

    p_run = sub.add_parser("run", help="Start the web app (uvicorn)")
    p_run.add_argument("--host", default=None, help="Bind host")
    p_run.add_argument("--port", type=int, default=None, help="Bind port")
    reload_group = p_run.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", dest="reload", action="store_true", default=None, help="Enable auto-reload"
    )
    reload_group.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )
    p_run.set_defaults(func=cmd_run, reload=None)

    p_users = sub.add_parser("users", help="List users in the database")
    p_users.set_defaults(func=cmd_users)

    p_report = sub.add_parser(
        "report",
        help=(
            "Build submission package: merge docs/judge.md, package docs/transcripts/, "
            "write docs/report.pdf (Guide pulls chats + runs student-judge first)"
        ),
    )
    p_report.add_argument("--name", required=True, help="Student name (printed on the PDF cover)")
    p_report.add_argument("--id", dest="student_id", required=True, help="Student ID (PDF only)")
    p_report.add_argument("--src", default=None, help="Markdown path (default: docs/report.md)")
    p_report.add_argument("--output", default=None, help="PDF path (default: docs/report.pdf)")
    p_report.set_defaults(func=cmd_report)

    p_transcripts = sub.add_parser(
        "transcripts",
        help="Package agent-written docs/transcripts/*.md into INDEX + zip (no IDE scrape)",
    )
    p_transcripts.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip writing docs/transcripts.zip",
    )
    p_transcripts.set_defaults(func=cmd_transcripts)

    p_usecase = sub.add_parser(
        "usecase",
        help="Render docs/diagrams/use-case.json to a UML use-case PNG",
    )
    p_usecase.add_argument("--spec", default=None, help="JSON spec (default: docs/diagrams/use-case.json)")
    p_usecase.add_argument("--output", default=None, help="PNG path (default: docs/diagrams/use-case.png)")
    p_usecase.set_defaults(func=cmd_usecase)

    p_skills_verify = sub.add_parser(
        "skills-verify",
        help="Check course skills against .agents/skills.lock.json",
    )
    p_skills_verify.set_defaults(func=cmd_skills_verify)

    p_skills_lock = sub.add_parser(
        "skills-lock",
        help="Rewrite .agents/skills.lock.json (course authors; needs FASTSTARTER_SKILLS_LOCK=1)",
    )
    p_skills_lock.set_defaults(func=cmd_skills_lock)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
