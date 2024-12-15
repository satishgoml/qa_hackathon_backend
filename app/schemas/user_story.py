
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Status(str, Enum):
    NEW = "New"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


# Pydantic Model for User Story
class UserStory(BaseModel):
    title: str = Field(..., description="Title of the user story")
    description: str = Field(..., description="Detailed description of the user story")
    acceptance_criteria: str = Field(
        ..., description="Point wise Acceptance criteria for the user story which will be used to generate test cases"
    )
    priority: Priority = Field(..., description="Priority level of the user story")
    story_points: Optional[int] = Field(
        None, description="Story points estimation", ge=1, le=13
    )
    status: Status = Field(
        default=Status.NEW, description="Current status of the user story"
    )