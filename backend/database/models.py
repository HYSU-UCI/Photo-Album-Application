import time
import uuid

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

from .connection import engine

__all__ = ["Base", "Images", "Tags", "ImageTags", "init_models"]

CONNECT_TIMEOUT = 20

Base = declarative_base()


class Images(Base):
    __tablename__ = "images"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False
    )
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)

    tags = relationship("Tags", secondary="image_tags", back_populates="images", lazy="selectin")


class Tags(Base):
    __tablename__ = "tags"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False
    )
    name = Column(String, unique=True, nullable=False)

    images = relationship("Images", secondary="image_tags", back_populates="tags", lazy="selectin")


class ImageTags(Base):
    __tablename__ = "image_tags"

    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), primary_key=True, nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True, nullable=False)


async def init_models() -> None:
    for _ in range(CONNECT_TIMEOUT):
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            return
        except OSError:
            time.sleep(1)
