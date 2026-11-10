
## Integration Test Plan

### 1. Objective

Verify that the Student Awards application's services, repositories, models, and database work together to support its main workflows.

### 2. Testing Approach

The existing tests create an isolated in-memory SQLite database. They exercise real application components without changing the deployed PostgreSQL database.

### 3. Integration Test Cases

The tests call service and CLI helper functions directly; they do not exercise HTTP routes.

| Test | Dependencies | Description |
|---|---|---|
| `test_submit_and_review_flow` | In-memory SQLite `create_engine`, `SQLModel.metadata.create_all`, `Session`; `add_reviewer`; `VolunteerService.create_submission()` and `review_submission()`; `VolunteerSubmissionRepository.create()` and `update_status()`; `AdministratorRepository.get_or_create_for_user()`; Student Awards and User models. | A submission for 4 volunteer hours is created with `pending` status and a non-null activity date. Approving it with the reviewer records `approved` status and that reviewer's administrator ID. |
| `test_student_service_resolves_user_to_different_student_id` | In-memory SQLite `create_engine`, `SQLModel.metadata.create_all`, `Session`; `VolunteerService.get_or_create_student_for_user()`, `create_submission_for_user()`, and `get_student_summary()`; `StudentRepository.get_or_create_for_user()` and `get_by_user_id()`; `VolunteerSubmissionRepository.create()`, `list_for_student()`, and `list_approved_for_student()`; User, Student, and VolunteerSubmission models. | A user with ID `13` is associated with a pre-existing Student record with ID `11`. The service resolves that student, saves the new submission with `student_id=11`, and reports a submission count of `1` for the student. |
| `test_milestone_unlock_and_award_redemption` | In-memory SQLite `create_engine`, `SQLModel.metadata.create_all`, `Session`; `add_reviewer`; `VolunteerService.create_submission()`, `review_submission()`, `get_or_create_student()`, `sync_student_hours()`, `list_milestones_for_student()`, `redeem_award()`, `review_redemption()`, and `list_awards_for_student()`; `VolunteerSubmissionRepository`, `AdministratorRepository`, `StudentRepository`, `MilestoneRepository`, `AwardRepository`, `StudentMilestoneRepository`, and `RedeemedAwardRepository`; Student Awards and User models. | Approving a 10-hour submission unlocks the 10-hour milestone and associates the campus-merch award with it. The eligible student can request that award; its redemption starts `pending` and can be marked `rejected` by the reviewer. The award is then shown as redeemed with rejected status, and a second request raises `ValueError`. |
| `test_demo_seed_data_is_consistent_and_rerunnable` | In-memory SQLite `create_engine`, `SQLModel.metadata.create_all`, `Session`, `session.exec(select(...))`; `app.cli._seed_demo_data()`; `UserRepository.get_by_username()` and `create()`; `StudentRepository.get_or_create_for_user()`; `AdministratorRepository.get_or_create_for_user()`; `VolunteerService.get_student_summary()`, `list_for_review()`, `list_submissions_for_admin()`, `get_submission_detail_for_admin()`, and `list_pending_redemptions()`; `verify_password()`; Student Awards and User models. | The first seed call reports `13` created and `0` skipped. The seeded users, students, administrators, submissions, milestones, awards, student milestones, and redemptions meet the asserted counts and consistency rules. After usernames and passwords are changed to legacy values and seeding runs again, there are still `30` submissions and `6` redemptions, and the student credentials and usernames are restored as asserted. |
| `test_legacy_bob_account_is_migrated_without_losing_student_history` | In-memory SQLite `create_engine`, `SQLModel.metadata.create_all`, `Session`, `session.exec(select(...))`; `app.cli._seed_demo_data()`; `UserRepository.get_by_username()`; `StudentRepository.get_or_create_for_user()`; `encrypt_password()` and `verify_password()`; User and Student models. | Seeding a legacy `bob` user with a Bruce Wayne student record preserves the original user and student IDs while renaming that account to Bruce Wayne. A separate `bob` user and Bob student are created, with the expected student names and passwords for both accounts. |
| `test_seed_adds_description_column_to_legacy_submission_table` | In-memory SQLite `create_engine`; `engine.begin()`; SQLAlchemy `text()` and `inspect()`; `app.cli._ensure_submission_description_column()`. | Given a legacy `volunteersubmission` table containing only `id`, the helper adds a column named `description`. |
| `test_seed_adds_and_backfills_activity_date_column` | In-memory SQLite `create_engine`; `engine.begin()` and `engine.connect()`; SQLAlchemy `text()` and `inspect()`; `app.cli._ensure_submission_activity_date_column()`. | Given a legacy submission with `submission_date='2026-09-15 12:30:00'` and no `activity_date` column, the helper adds the column and backfills the row's activity date to `2026-09-15`. |

### 4. Entry Criteria

- Application models, services, and repositories are available.
- pytest and database dependencies are installed.
- The test database can be initialized.
