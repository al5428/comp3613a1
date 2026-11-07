from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.volunteer_service import VolunteerService


@pytest.fixture
def service():
    volunteer_service = VolunteerService(db=Mock())
    volunteer_service.repo = Mock()
    volunteer_service.student_repo = Mock()
    volunteer_service.milestone_repo = Mock()
    volunteer_service.award_repo = Mock()
    volunteer_service.student_milestone_repo = Mock()
    volunteer_service.redemption_repo = Mock()
    volunteer_service.administrator_repo = Mock()
    return volunteer_service


def test_empty_activity_name(service):
    with pytest.raises(ValueError, match="Activity name is required"):
        service.create_submission(
            student_id=1,
            activity_name="   ",
            hours_worked=1,
            evidence="",
        )

    service.repo.create.assert_not_called()


def test_zero_volunteer_hours(service):
    with pytest.raises(ValueError, match="Hours worked must be greater than zero"):
        service.create_submission(
            student_id=1,
            activity_name="Campus garden",
            hours_worked=0,
            evidence="",
        )

    service.repo.create.assert_not_called()


def test_approved_hours(service):
    service.repo.list_approved_for_student.return_value = [
        SimpleNamespace(hours_worked=5),
        SimpleNamespace(hours_worked=10),
    ]

    assert service.get_total_approved_hours(student_id=1) == 15
    service.repo.list_approved_for_student.assert_called_once_with(1)


def test_invalid_review_decision(service):
    with pytest.raises(ValueError, match="Decision must be approved or rejected"):
        service.review_submission(submission_id=1, decision="pending")

    service.repo.update_status.assert_not_called()
    service.administrator_repo.get_or_create_for_user.assert_not_called()


def test_ineligible_redemption(service):
    service.sync_student_hours = Mock(
        return_value=SimpleNamespace(total_volunteer_hours=20)
    )
    service.award_repo.get_by_id.return_value = SimpleNamespace(
        required_hours=25
    )

    with pytest.raises(ValueError, match="does not yet meet the hour requirement"):
        service.redeem_award(student_id=1, award_id=2)

    service.redemption_repo.get_by_student_and_award.assert_not_called()
    service.redemption_repo.create.assert_not_called()


def test_duplicate_redemption(service):
    service.sync_student_hours = Mock(
        return_value=SimpleNamespace(total_volunteer_hours=25)
    )
    service.award_repo.get_by_id.return_value = SimpleNamespace(
        required_hours=25
    )
    service.redemption_repo.get_by_student_and_award.return_value = object()

    with pytest.raises(ValueError, match="already been requested"):
        service.redeem_award(student_id=1, award_id=2)

    service.redemption_repo.get_by_student_and_award.assert_called_once_with(1, 2)
    service.redemption_repo.create.assert_not_called()


def test_award_eligibility(service):
    award = SimpleNamespace(
        id=2,
        name="Medal",
        description="A 50-hour award",
        required_hours=50,
        milestone_id=3,
    )
    service.sync_student_hours = Mock()
    service.get_total_approved_hours = Mock(return_value=25)
    service.award_repo.list_all.return_value = [award]
    service.milestone_repo.get_by_id.return_value = SimpleNamespace(
        name="Community Builder"
    )
    service.redemption_repo.get_by_student_and_award.return_value = None

    awards = service.list_awards_for_student(student_id=1)

    assert awards == [
        {
            "id": 2,
            "name": "Medal",
            "description": "A 50-hour award",
            "required_hours": 50,
            "milestone_name": "Community Builder",
            "eligible": False,
            "redeemed": False,
            "status": "not_requested",
            "hours_remaining": 25,
        }
    ]
    service.sync_student_hours.assert_called_once_with(1)
    service.get_total_approved_hours.assert_called_once_with(1)
    service.redemption_repo.get_by_student_and_award.assert_called_once_with(1, 2)


def test_invalid_redemption_review(service):
    with pytest.raises(ValueError, match="Decision must be approved or rejected"):
        service.review_redemption(redemption_id=1, decision="cancelled")

    service.redemption_repo.update_status.assert_not_called()
    service.administrator_repo.get_or_create_for_user.assert_not_called()
