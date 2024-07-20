from uuid import UUID

from pydantic import BaseModel


class Image(BaseModel):
    id: UUID
    filename: str
    mime_type: str

    class Config:
        orm_mode = True


class Tag(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True


class AddTag(BaseModel):
    name: str


class ReplaceTag(BaseModel):
    id: UUID
    name: str


class TagQuery(BaseModel):
    tags_id: list[UUID] = []


class ImageMetadata(BaseModel):
    tags: list[Tag] = []
    filename: str
