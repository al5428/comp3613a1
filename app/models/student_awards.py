from datetime import date,datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    total_volunteer_hours: int = Field(default=0)



class Administrator(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    name: str = Field(index=True)
    email: str = Field(index=True)



class Milestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    required_hours: int = Field(default=0)
    description: str = ""

    student_milestones: list["StudentMilestone"] = Relationship(back_populates="milestone")
    # student-build:code-check model
    # Add the ORM navigation field for earned StudentMilestone records.



class StudentMilestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    milestone_id: int = Field(foreign_key="milestone.id", index=True)
    date_awarded: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    milestone: "Milestone" = Relationship(back_populates="student_milestones")
    # student-build:code-check model
    # Add the matching ORM navigation field to Milestone; keep the existing FK.



class Award(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    required_hours: int = Field(default=0)
    milestone_id: int = Field(foreign_key="milestone.id", index=True)



class VolunteerSubmission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)

    # student-build:code-check model
    # Add a required activity_date field; submission_date remains the system timestamp.
    activity_date: date = Field(default_factory=date.today)

    activity_name: str = Field(index=True)
    description: str = ""
    hours_worked: int = Field(default=0)
    submission_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = Field(default="pending", index=True)
    evidence: str = ""
    administrator_id: Optional[int] = Field(
        default=None,
        foreign_key="administrator.id"
    )
    review_notes: str = ""
    reviewed_at: Optional[datetime] = Field(default=None)
    
    @property
    def reviewer_id(self):
        return self.administrator_id

    @reviewer_id.setter
    def reviewer_id(self, value):
        self.administrator_id = value


class RedeemedAward(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    award_id: int = Field(foreign_key="award.id", index=True)
    redemption_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending", index=True)
    administrator_id: Optional[int] = Field(default=None, foreign_key="administrator.id")

