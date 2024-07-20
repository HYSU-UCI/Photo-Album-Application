import os
from uuid import UUID

from config import get_settings
from database.models import Images
from database.models import ImageTags
from database.models import Tags
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import FileResponse
from schemas.models import AddTag
from schemas.models import ImageMetadata
from schemas.models import ReplaceTag
from schemas.models import TagQuery
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

VALID_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/gif"]


async def create_image_with_upload_file(session: AsyncSession, upload_file: UploadFile) -> Images:
    """
    Create an image in the database and save the image in the filesystem.
    """
    # Check if file content type is valid
    if upload_file.content_type not in VALID_MIME_TYPES:
        raise HTTPException(
            status_code=400, detail=f"File type: {upload_file.content_type} is not supported"
        )

    # Save image into database
    image_instance = Images(
        filename=os.path.basename(upload_file.filename), mime_type=upload_file.content_type
    )
    session.add(image_instance)
    await session.commit()

    # Save image into filesystem based on the image id
    await session.refresh(image_instance)
    image_local_path = os.path.join(get_settings().uploads_path, str(image_instance.id))
    with open(image_local_path, "wb") as f:
        f.write(await upload_file.read())

    return image_instance


async def delete_image_by_id(session: AsyncSession, image_id: UUID) -> None:
    """
    Delete an image from the database and filesystem.
    """
    # Delete image from database, and delete orphan tags
    image_instance = await session.get(Images, image_id)
    if image_instance is None:
        raise HTTPException(status_code=404, detail="Image not found")
    tags = image_instance.tags
    for tag in tags:
        stmt = select(ImageTags).where(ImageTags.tag_id == tag.id)
        result = (await session.execute(stmt)).scalars().all()
        if len(result) == 1:
            await session.delete(result[0])
            await session.delete(tag)
    await session.delete(image_instance)
    await session.commit()

    # Delete image from filesystem
    image_local_path = os.path.join(get_settings().uploads_path, str(image_id))
    os.remove(image_local_path)


async def get_image_response_by_id(session: AsyncSession, image_id: UUID) -> FileResponse:
    """
    Get an image from the filesystem and return it as a FileResponse.
    """
    # Get image from database
    image_instance = await session.get(Images, image_id)
    if image_instance is None:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get image from filesystem
    image_local_path = os.path.join(get_settings().uploads_path, str(image_id))
    return FileResponse(image_local_path, media_type=image_instance.mime_type)


async def get_image_info_by_id(session: AsyncSession, image_id: UUID) -> ImageMetadata:
    image_instance = await session.get(Images, image_id)

    if image_instance is None:
        raise HTTPException(status_code=404, detail="Image not found")

    img_instance = await session.get(Images, image_id)
    metadata = ImageMetadata(filename=img_instance.filename)

    for tag_instance in image_instance.tags:
        metadata.tags.append(tag_instance)

    return metadata


async def search_image_by_tags(session: AsyncSession, query: TagQuery) -> list[Images]:
    """
    Get images from the database based on the tags.
    """
    stmt = (
        select(Images)
        .join(ImageTags)
        .where(ImageTags.tag_id.in_(query.tags_id))
        .group_by(Images.id)
        .having(func.count(ImageTags.tag_id) == len(query.tags_id))
    )
    images = (await session.execute(stmt)).scalars().all()

    return images


async def list_image_by_limit(session: AsyncSession, offset: int, limit: int) -> list[Images]:
    stmt = select(Images).offset(offset).limit(limit)
    return (await session.execute(stmt)).scalars().all()


async def add_tag_to_image(session: AsyncSession, image_id: UUID, tag: AddTag) -> Tags:
    """
    Add a tag to the database if tag does not exist and create an association between the image and the tag.
    """
    # Make sure image exist
    image_instance = await session.get(Images, image_id)
    if image_instance is None:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get or create tag
    tag_instance = (await session.execute(select(Tags).where(Tags.name == tag.name))).scalar()
    if tag_instance is None:
        tag_instance = Tags(name=tag.name)
        session.add(tag_instance)
        await session.flush()

    # Create association
    image_tag_instance = await session.get(ImageTags, (image_id, tag_instance.id))
    if image_tag_instance is not None:
        raise HTTPException(status_code=400, detail="Image already has this tag")
    image_tag_instance = ImageTags(image_id=image_id, tag_id=tag_instance.id)
    session.add(image_tag_instance)
    await session.commit()

    return tag_instance


async def replace_tag_of_image(session: AsyncSession, image_id: UUID, tag: ReplaceTag) -> Tags:
    """
    Replace the association between an image and a tag with a new tag.
    """
    # Make sure this association exist
    image_tag_instance = await session.get(ImageTags, (image_id, tag.id), populate_existing=True)
    if image_tag_instance is None:
        raise HTTPException(status_code=404, detail="Image or tag not found")

    # Try to get the tag from the database, if it does not exist, create it
    tag_instance = (await session.execute(select(Tags).where(Tags.name == tag.name))).scalar()
    if tag_instance is not None:
        # If image already has association with the new tag, raise an error
        if await session.get(ImageTags, (image_id, tag_instance.id)) is not None:
            raise HTTPException(status_code=400, detail="Image already has this tag")
    else:
        tag_instance = Tags(name=tag.name)
        session.add(tag_instance)
        await session.flush()
    await session.delete(image_tag_instance)

    # Create association
    image_tag_instance = ImageTags(image_id=image_id, tag_id=tag_instance.id)
    session.add(image_tag_instance)
    await session.commit()

    # delete tag if the deleted association is the last one that uses this tag
    stmt = select(ImageTags).where(ImageTags.tag_id == tag.id)
    if not (await session.execute(stmt)).scalars().all():
        await session.delete(await session.get(Tags, tag.id))
        await session.commit()

    return tag_instance


async def delete_tag_of_image(session: AsyncSession, image_id: UUID, tag_id: UUID) -> None:
    """
    Delete an association between an image and a tag.
    """
    image_tag_instance = await session.get(ImageTags, (image_id, tag_id))
    if image_tag_instance is None:
        raise HTTPException(status_code=404, detail="Image or tag not found")

    await session.delete(image_tag_instance)
    await session.commit()

    # delete tag if the deleted association is the last one that uses this tag
    stmt = select(ImageTags).where(ImageTags.tag_id == tag_id)
    if not (await session.execute(stmt)).scalars().all():
        await session.delete(await session.get(Tags, tag_id))
        await session.commit()


async def list_tags(session: AsyncSession) -> list[Tags]:
    """
    Get all tags from the database.
    """
    stmt = select(Tags)
    tags = (await session.execute(stmt)).scalars().all()

    return tags
