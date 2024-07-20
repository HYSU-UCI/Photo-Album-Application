from uuid import UUID

import utils.crud
from database.connection import get_db
from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import status
from schemas.models import AddTag
from schemas.models import Image
from schemas.models import ImageMetadata
from schemas.models import ReplaceTag
from schemas.models import Tag
from schemas.models import TagQuery
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["router"]

router = APIRouter(tags=["api"])


@router.post("/images/create", status_code=status.HTTP_201_CREATED, response_model=Image)
async def create_image(image: UploadFile, db_session: AsyncSession = Depends(get_db)):
    image = await utils.crud.create_image_with_upload_file(db_session, image)
    return image


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: UUID, db_session: AsyncSession = Depends(get_db)):
    await utils.crud.delete_image_by_id(db_session, image_id)
    return None


@router.post("/images/search", status_code=status.HTTP_200_OK, response_model=list[Image])
async def search_image(query: TagQuery, db_session: AsyncSession = Depends(get_db)):
    return await utils.crud.search_image_by_tags(db_session, query)


@router.get("/images/list", status_code=status.HTTP_200_OK, response_model=list[Image])
async def list_images(offset: int = 0, limit: int = 20, db_session: AsyncSession = Depends(get_db)):
    return await utils.crud.list_image_by_limit(db_session, offset, limit)


@router.get("/images/{image_id}", status_code=status.HTTP_200_OK, response_model=ImageMetadata)
async def get_image(image_id: UUID, db_session: AsyncSession = Depends(get_db)):
    return await utils.crud.get_image_info_by_id(db_session, image_id)


@router.post("/images/{image_id}/tags", status_code=status.HTTP_201_CREATED, response_model=Tag)
async def add_tag_to_image(image_id: UUID, tag: AddTag, db_session: AsyncSession = Depends(get_db)):
    tag_instance = await utils.crud.add_tag_to_image(db_session, image_id, tag)
    return tag_instance


@router.put("/images/{image_id}/tags", status_code=status.HTTP_200_OK, response_model=Tag)
async def replace_tag_of_image(image_id: UUID, tag: ReplaceTag, db_session=Depends(get_db)):
    tag_instance = await utils.crud.replace_tag_of_image(db_session, image_id, tag)
    return tag_instance


@router.delete("/images/{image_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_of_image(image_id: UUID, tag_id: UUID, db_session=Depends(get_db)):
    await utils.crud.delete_tag_of_image(db_session, image_id, tag_id)
    return None


@router.get("/tags/list", status_code=status.HTTP_200_OK, response_model=list[Tag])
async def list_tags(db_session: AsyncSession = Depends(get_db)):
    return await utils.crud.list_tags(db_session)
