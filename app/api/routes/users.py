from typing import Any
from fastapi import APIRouter
from pocketbase.models import Record

from app.api.deps import CurrentUser

router = APIRouter()

@router.get("/me")
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user.__dict__
