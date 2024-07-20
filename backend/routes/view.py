from uuid import UUID

import utils.crud
from database.connection import get_db
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["router"]

router = APIRouter(tags=["view"])


@router.get("/images/{image_id}", response_class=FileResponse)
async def get_image(image_id: UUID, db_session: AsyncSession = Depends(get_db)):
    return await utils.crud.get_image_response_by_id(db_session, image_id)
