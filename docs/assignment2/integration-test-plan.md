
## Integration Test Plan

### 1. Objective

Verify that the Student Awards application's services, repositories, models, and database work together to support its main workflows.

### 2. Testing Approach

The existing tests create an isolated in-memory SQLite database. They exercise real application components without changing the deployed PostgreSQL database.

### 3. Integration Test Cases

The table follows Tutorial 4's **Test / Dependencies / Description** format.

| Test | Dependencies | Description |
|---|---|---|
| **IT01** `test_submit_and_review_flow` | Submission service, review service, repositories, database | A submission starts as pending and is approved by the correct administrator. |
| **IT02** `test_student_service_resolves_user_to_different_student_id` | Student lookup, submission service, database | A submission uses the correct student ID even when it differs from the user ID. |
| **IT03** `test_milestone_unlock_and_award_redemption` | Submission review, hour synchronization, milestones, redemptions | Approved hours unlock a milestone; redemption can be reviewed; a duplicate request is blocked. |
| **IT04** `test_demo_seed_data_is_consistent_and_rerunnable` | Seed function, models, repositories, database | Demo records remain consistent when seeding is repeated. |
| **IT05** `test_legacy_bob_account_is_migrated_without_losing_student_history` | Seed function, user and student models, database | Legacy student identity and records are preserved during migration. |
| **IT06** `test_seed_adds_description_column_to_legacy_submission_table` | Schema update helper, database | A missing `description` column is added to a legacy table. |
| **IT07** `test_seed_adds_and_backfills_activity_date_column` | Schema update helper, database | A missing `activity_date` column is added and existing dates are backfilled. |

### 4. Entry Criteria

- Application models, services, and repositories are available.
- pytest and database dependencies are installed.
- The test database can be initialized.
