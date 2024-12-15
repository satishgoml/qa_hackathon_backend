from fastapi import APIRouter, HTTPException, Depends
from pocketbase import PocketBase
from app.src.test_case_generator import TestCaseGenerator
from app.api.deps import CurrentUser, PocketBaseDep

router = APIRouter()


@router.post("/generate_from_user_story")
async def generate_and_save_test_cases(
    user_story_id: str,
    current_user: CurrentUser,
    pb: PocketBaseDep,
):
    """
    Generate and save test cases for a specific user story.

    Args:
        user_story_id (str): The ID of the user story to generate test cases for.
        current_user (CurrentUser): The currently authenticated user.
        pb (PocketBaseDep): The PocketBase dependency for database interaction.

    Returns:
        dict: A message indicating the success of the operation.
    """
    try:
        # Fetch the user story details
        user_story = pb.collection("user_story").get_one(user_story_id)
        if not user_story:
            raise HTTPException(status_code=404, detail="User story not found.")

        # Extract user story details
        story_text = user_story.title
        acceptance_criteria = user_story.acceptance_criteria
        if not story_text or not acceptance_criteria:
            raise HTTPException(
                status_code=400,
                detail="User story or acceptance criteria is missing.",
            )

        # Initialize TestCaseGenerator
        test_case_generator = TestCaseGenerator()

        # Generate test cases for the user story
        test_cases = test_case_generator.generate_test_cases(
            user_story=story_text,
            acceptance_criteria=acceptance_criteria,
        )

        # Save the generated test cases to PocketBase
        for test_case in test_cases.test_cases:
            pb.collection("test_case").create(
                {
                    "user_story": user_story_id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "preconditions": test_case.preconditions,
                    "steps": test_case.steps,
                    "expected_result": test_case.expected_result,
                    "created_by": current_user.id,
                }
            )

        return {"message": "Test cases generated and saved successfully."}

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise e
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
