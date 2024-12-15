import logging
from sqlalchemy import text
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from mangum import Mangum
from sqlmodel import Session, SQLModel

import sys


sys.path.append("")

from app.api.main import api_router
from app.core.config import settings

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )




@app.get("/")
def read_root():
    return {"message": "Welcome to the QA API!"}


app.include_router(api_router, prefix=settings.API_V1_STR)

# Create a handler for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dev", action="store_true", help="Run in development mode"
    )
    args = parser.parse_args()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=args.dev,  # Enable auto-reload in dev mode
        workers=1 if args.dev else 4,  # Single worker in dev mode
    )
