"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

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

__all__ = [
    "User",
    "Student",
    "Administrator",
    "Milestone",
    "StudentMilestone",
    "Award",
    "VolunteerSubmission",
    "RedeemedAward",
]
