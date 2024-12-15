from typing import Annotated
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pocketbase import PocketBase
from pocketbase.models import Record

from app.core.config import settings


def get_pocketbase() -> PocketBase:
    return PocketBase(settings.POCKETBASE_URL)


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials or not credentials.scheme == "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme")
        return credentials.credentials


TokenDep = Annotated[str, Depends(TokenBearer())]


PocketBaseDep = Annotated[PocketBase, Depends(get_pocketbase)]


def get_current_user(token: TokenDep, pb: PocketBaseDep):
    try:
        print("Token", token)
        pb.auth_store.save(token, None)
        pb.collection("users").auth_refresh()   
        pb_user = pb.auth_store.model
        if not pb_user:
            raise HTTPException(status_code=403, detail="Invalid authentication token")
        return pb_user
    except Exception as e:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


CurrentUser = Annotated[Record, Depends(get_current_user)]
