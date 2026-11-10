## User Acceptance Test Report

| Tester Information | Details |
|---|---|
| Tester Name | **Edan Ali** |
| Tester Position/Role | **Student Developer** |
| Date of Test (DD/MM/YYYY) | **07/11/2026** |

### Application and Environment

| Item | Details |
|---|---|
| Application | Student Awards web application |
| Platform | Web browser |
| Environment | Deployed application |
| Test data | Demo accounts, volunteer submissions, milestones, and awards; individual account credentials are not recorded here. |

### User Acceptance Test Cases

| Test Case | Pre-conditions | Test Steps | Test Criteria | Success (Pass/Fail) |
|---|---|---|---|---|
| **UAT01 — Submit volunteer hours** | Student is signed in to the deployed Student Awards application and can access Volunteer Hours. | 1. Open **Volunteer Hours**.<br>2. Enter the recorded activity **Community Cleanup** and **6** hours, with the activity details required by the form.<br>3. Submit the activity for review. | The submission history shows **Community Cleanup**, **6h**, and **Pending**.<br>Evidence: [UAT01 screenshot](screenshots/uat01-submit-hours.png) | **Pass** — recorded |
| **UAT02 — Admin approves volunteer hours** | Administrator is signed in, and a pending **Community Cleanup** submission for **6** hours is available for review. | 1. Open the administrator's **Volunteer Hours** list.<br>2. Locate the **Community Cleanup** entry showing **6** hours.<br>3. Approve the submission. | The page confirms the submission was marked approved, and the administrator's list shows **Community Cleanup**, **6** hours, and **Approved**.<br>Evidence: [UAT02 screenshot](screenshots/uat02-approve-submission.png). The screenshot matches UAT01 by activity name and hours but does not show a submission ID to confirm it is the same record. | **Pass** — recorded |
| **UAT03 — Admin rejects volunteer hours** | Administrator is signed in, and the **Beach Cleanup** submission for **3** hours is pending review. | 1. Open the administrator's **Volunteer Hours** list.<br>2. Locate **Beach Cleanup**, showing **3** hours.<br>3. Reject the submission. | The page confirms the submission was marked rejected, and the list shows **Beach Cleanup**, **3** hours, and **Rejected**.<br>Evidence: [UAT03 screenshot](screenshots/uat03-reject-submission.png) | **Pass** — recorded |
| **UAT04 — View approved volunteer hours total** | Student Bob is signed in with the recorded progress snapshot: **3** submissions, including approved hours and a rejected **3-hour** Beach Cleanup submission. | 1. Open the student **Dashboard**.<br>2. Read the **Approved**, **Pending**, and **Submissions** summary values.<br>3. Compare the approved total with the rejected Beach Cleanup entry. | The dashboard shows **11h Approved**, **0 Pending**, and **3 Submissions**; the rejected **3** hours are not included in the approved total. This is the earlier progress snapshot, before the additional approved hours shown in UAT05.<br>Evidence: [UAT04 screenshot](screenshots/uat04-view-progress.png) | **Pass** — recorded |
| **UAT05 — Unlock milestone plaque at 25 approved hours** | Student Bob is signed in after additional approved hours have brought the recorded total to **25**. | 1. Open the student **Dashboard**.<br>2. Read the approved-hour total and the **Plaque Milestone** card. | The dashboard shows **25h Approved**; the Plaque Milestone shows **Unlocked**, **25 / 25 approved hours**, and **100%** progress.<br>Evidence: [UAT05 screenshot](screenshots/uat05-unlock-plaque.png) | **Pass** — recorded |
| **UAT06 — Submit milestone redemption request** | Student is signed in, has at least **25 approved hours**, and has not already requested the Plaque award. | 1. Open **Awards**.<br>2. Locate **Plaque**, which requires **25** approved hours.<br>3. Request the Plaque award redemption. | The Awards page confirms the request and displays the Plaque award with **pending** status.<br>Evidence: [UAT06 screenshot](screenshots/uat06-redeem-award.png) | **Pass** — recorded |
| **UAT07 — Prevent duplicate redemption** | Student is signed in and already has a pending redemption request for the Plaque award. | 1. Open **Awards** after submitting the existing request.<br>2. Inspect the Plaque award and available actions. | The Plaque award remains **pending**, and no second redemption action is available through the student interface.<br>Evidence: [UAT07 screenshot](screenshots/uat07-block-duplicate.png) | **Pass** — recorded |
| **UAT08 — Admin approves redemption request** | Administrator is signed in, and Bob's Plaque award redemption request is available for review. | 1. Open the administrator's award redemption review page.<br>2. Locate Bob's Plaque request.<br>3. Approve the redemption. | The Awards page displays the Plaque award with **approved** status after review.<br>Evidence: [UAT08 screenshot](screenshots/uat08-review-redemption.png) | **Pass** — recorded |

### UAT Summary

The existing report records **8/8 UAT cases as passed**. Tester name, tester position/role, and test date were not present in the available evidence and must be completed from the original test record.
