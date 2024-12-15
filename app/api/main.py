from fastapi import APIRouter, Depends

from .deps import get_current_user

api_router = APIRouter()

# Include all the route modules here
from .routes import users
from .routes import user_story
from .routes import test_case

# Combine all routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)

api_router.include_router(
    user_story.router,
    prefix="/user_story",
    tags=["user-story"],
    dependencies=[Depends(get_current_user)],
)

api_router.include_router(
    test_case.router,
    prefix="/test_case",
    tags=["test-case"],
    dependencies=[Depends(get_current_user)],
)
