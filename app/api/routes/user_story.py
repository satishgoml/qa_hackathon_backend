import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pocketbase import PocketBase
from typing import List, Annotated

import requests
from app.schemas.user_story import UserStory
from app.src.user_story_generator import UserStoryGenerator
from app.api.deps import CurrentUser, PocketBaseDep
import tempfile
import os

router = APIRouter()


@router.post("/generate_from_pdf")
async def generate_and_save_user_stories(
    project_id: str,
    current_user: CurrentUser,
    pb: PocketBaseDep,
):
    try:

        # # Get project and BRD document
        project = pb.collection("project").get_one(project_id)
        brd_file = pb.collection("projects").get_file_url(project, project.brd_document)
        

        # Download and save BRD temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            response = requests.get(brd_file)
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name

        # Initialize generator and process PDF
        generator = UserStoryGenerator(
            pb = pb
        )
        chunks = generator.extract_text_from_pdf(tmp_file_path)
        generator.generate_user_stories(chunks, project_id, current_user.id)
    # # Cleanup temporary file
        os.unlink(tmp_file_path)

        return {
            "message": "User stories created successfully",
            # "count": len(user_stories),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
