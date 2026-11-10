
## Unit Test Plan

### 1. Objective

Verify that individual methods in `VolunteerService` handle validation, approved-hour calculations, and award redemption rules correctly without using a real database.

### 2. Testing Approach

Each test targets one method. Repository and database dependencies will be replaced with mocks so tests are independent and repeatable.

### 3. Unit Test Cases

The table below documents the eight existing tests in `tests/test_volunteer_service_unit.py`, including their test inputs and asserted behavior.

| Unit Test | Input | Expected Output |
|---|---|---|
| `test_empty_activity_name` | Call `create_submission(student_id=1, activity_name="   ", hours_worked=1, evidence="")`. | Raises `ValueError` with message `"Activity name is required."`; `repo.create` is not called. |
| `test_zero_volunteer_hours` | Call `create_submission(student_id=1, activity_name="Campus garden", hours_worked=0, evidence="")`. | Raises `ValueError` with message `"Hours worked must be greater than zero."`; `repo.create` is not called. |
| `test_approved_hours` | For student `1`, mock two approved submissions with `hours_worked=5` and `hours_worked=10`; call `get_total_approved_hours(student_id=1)`. | Returns `15`; `repo.list_approved_for_student` is called once with `1`. |
| `test_invalid_review_decision` | Call `review_submission(submission_id=1, decision="pending")`. | Raises `ValueError` with message `"Decision must be approved or rejected."`; `repo.update_status` and `administrator_repo.get_or_create_for_user` are not called. |
| `test_ineligible_redemption` | For student `1`, mock synchronized hours as `20` and award `2` as requiring `25` hours; call `redeem_award(student_id=1, award_id=2)`. | Raises `ValueError` with message `"Student does not yet meet the hour requirement for this award."`; the redemption lookup and `redemption_repo.create` are not called. |
| `test_duplicate_redemption` | For student `1`, mock synchronized hours as `25`, award `2` as requiring `25` hours, and an existing redemption; call `redeem_award(student_id=1, award_id=2)`. | Raises `ValueError` with message `"This award has already been requested and cannot be redeemed again."`; `get_by_student_and_award` is called once with `(1, 2)` and `redemption_repo.create` is not called. |
| `test_award_eligibility` | For student `1`, mock `25` approved hours and no existing redemption. Return award `2` named `"Medal"`, description `"A 50-hour award"`, requiring `50` hours and linked to milestone `3`, named `"Community Builder"`. | Returns `[{"id": 2, "name": "Medal", "description": "A 50-hour award", "required_hours": 50, "milestone_name": "Community Builder", "eligible": false, "redeemed": false, "status": "not_requested", "hours_remaining": 25}]`; hour synchronization and approved-hour lookup are each called once with `1`, and the redemption lookup is called once with `(1, 2)`. |
| `test_invalid_redemption_review` | Call `review_redemption(redemption_id=1, decision="cancelled")`. | Raises `ValueError` with message `"Decision must be approved or rejected."`; `redemption_repo.update_status` and `administrator_repo.get_or_create_for_user` are not called. |

### 4. Entry Criteria

- The Student Awards application source code is available.
- pytest and project dependencies are installed.
- Mocks can be configured for service dependencies.
