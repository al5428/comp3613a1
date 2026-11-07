
## Unit Test Plan

### 1. Objective

Verify that individual methods in `VolunteerService` handle validation, approved-hour calculations, and award redemption rules correctly without using a real database.

### 2. Testing Approach

Each test targets one method. Repository and database dependencies will be replaced with mocks so tests are independent and repeatable.

### 3. Unit Test Cases

The table follows Tutorial 4's **Unit Test / Module Tested / Expected Output** format.

| Unit Test | Module Tested | Expected Output |
|---|---|---|
| **UT01** `test_empty_activity_name` | `create_submission()` with an empty activity name | Raises `ValueError` |
| **UT02** `test_zero_volunteer_hours` | `create_submission()` with `hours_worked=0` | Raises `ValueError` |
| **UT03** `test_approved_hours` | `get_total_approved_hours()` with mocked approved submissions of 5 and 10 hours | Returns `15` |
| **UT04** `test_invalid_review_decision` | `review_submission()` with `decision="pending"` | Raises `ValueError` |
| **UT05** `test_ineligible_redemption` | `redeem_award()` with 20 approved hours and a 25-hour award | Raises `ValueError` |
| **UT06** `test_duplicate_redemption` | `redeem_award()` when a previous request exists | Raises `ValueError` |
| **UT07** `test_award_eligibility` | `list_awards_for_student()` with 25 hours and a 50-hour award | `eligible=False` and `hours_remaining=25` |
| **UT08** `test_invalid_redemption_review` | `review_redemption()` with `decision="cancelled"` | Raises `ValueError` |

### 4. Entry Criteria

- The Student Awards application source code is available.
- pytest and project dependencies are installed.
- Mocks can be configured for service dependencies.
