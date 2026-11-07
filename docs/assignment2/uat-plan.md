## User Acceptance Test Plan

### 1. Objective

Confirm that students and administrators can complete the main tasks shown in the Student Awards use cases and wireframes.

### 2. Test Environment

| Item | Details |
|---|---|
| Application | Student Awards web application |
| Platform | Web browser |
| Environment | Deployed application |
| Test participants | Student-role and administrator-role testers |
| Test data | Demo accounts, submissions, milestones, and awards |

### 3. Acceptance Test Cases

This table follows Tutorial 4's **Test Case / Pre-conditions / Test Steps / Test Criteria / Success** format.

| Test Case | Pre-conditions | Test Steps | Test Criteria | Success |
|---|---|---|---|:---:|
| **UAT01** Submit volunteer hours | Student is logged in. | Open Volunteer Hours; enter activity details; submit. | Submission appears as **Pending**. | ☑ |
| **UAT02** Approve submission | Administrator is logged in; a pending submission exists. | Open submission; review details; select Approve. | Status changes to **Approved**. | ☑ |
| **UAT03** Reject submission | Administrator is logged in; another pending submission exists. | Open submission; select Reject. | Status changes to **Rejected**. | ☑ |
| **UAT04** View progress | Student is logged in; submissions exist. | Open Dashboard; inspect volunteer-hour total. | Only approved hours count toward progress. | ☑ |
| **UAT05** Unlock milestone | Student has at least 25 approved hours. | Open Dashboard; inspect milestones. | **Plaque** is unlocked. | ☑ |
| **UAT06** Redeem award | Student is eligible and has not requested the award. | Open Awards; select award; request redemption. | Redemption is shown as **Pending**. | ☑ |
| **UAT07** Block duplicate redemption | Student has already requested the award. | Open Awards; inspect the previously requested award. | No second redemption option is available through the student interface. | ☑ |
| **UAT08** Review redemption | Administrator is logged in; a pending redemption exists. | Open request; approve or reject it. | Redemption displays the selected status. | ☑ |

### 4. Acceptance Criteria

A test passes when the tester can perform the stated steps and observe the expected result in the application interface without an unexpected error.

### 5. UAT Results Record

The following results were recorded after executing all eight User Acceptance Tests on the deployed Student Awards application.

| Test ID | Actual Result | Pass / Fail | Comments |
|---|---|:---:|---|
| UAT01 | Community Cleanup submitted successfully and displayed with Pending status. | ☑ Pass | Student successfully submitted 5 volunteer hours. |
| UAT02 | Administrator approved Community Cleanup, and its status changed to Approved. | ☑ Pass | Successfully approved the 5-hour submission. |
| UAT03 | Administrator rejected Beach Cleanup, and its status changed to Rejected. | ☑ Pass | Successfully rejected the 3-hour submission. |
| UAT04 | Dashboard displayed 11 approved hours, excluding the rejected 3-hour submission. | ☑ Pass | Milestone progress correctly reflects approved volunteer hours only. |
| UAT05 | Student reached 25 approved hours and the Plaque Milestone displayed Unlocked. | ☑ Pass | Plaque Milestone successfully unlocked at 25 approved hours. |
| UAT06 | Plaque Award redemption request displayed Pending status. | ☑ Pass | Student successfully requested the Plaque Award after reaching 25 approved hours. |
| UAT07 | Plaque Award displayed Pending status with no option to request redemption again. | ☑ Pass | Duplicate redemption prevented through the student interface. |
| UAT08 | Administrator approved Bob's Plaque Award redemption, and its status changed to Approved. | ☑ Pass | Award redemption successfully reviewed and approved. |

### 6. UAT Summary

All 8 User Acceptance Tests passed successfully. The Student Awards application supported volunteer-hour submission, administrator approval and rejection, student progress tracking, milestone unlocking, award redemption, and prevention of duplicate redemption through the student interface.

**Overall UAT Result: 8/8 Passed (100%)**