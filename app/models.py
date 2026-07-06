import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class ContentStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"


class Difficulty(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class PublishableMixin(TimestampMixin):
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    summary: Mapped[str] = mapped_column(String(300))
    body_md: Mapped[str] = mapped_column(Text)
    body_html: Mapped[str] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.draft
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reading_minutes: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(500))
    thumb_path: Mapped[str] = mapped_column(String(500))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    alt_text: Mapped[str] = mapped_column(String(300), default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PostTag(Base):
    __tablename__ = "post_tags"

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)


class Post(Base, PublishableMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hero_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("images.id"), nullable=True
    )

    hero_image: Mapped[Image | None] = relationship(Image, lazy="joined")
    tags: Mapped[list[Tag]] = relationship(
        Tag, secondary=PostTag.__table__, lazy="selectin"
    )


class Recipe(Base, PublishableMixin):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hero_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("images.id"), nullable=True
    )

    style: Mapped[str] = mapped_column(String(50))
    batch_liters: Mapped[float] = mapped_column(Float)
    og: Mapped[float | None] = mapped_column(Float, nullable=True)
    fg: Mapped[float | None] = mapped_column(Float, nullable=True)
    abv: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty))
    ingredients_json: Mapped[list] = mapped_column(JSON, default=list)
    steps_json: Mapped[list] = mapped_column(JSON, default=list)
    total_days: Mapped[int] = mapped_column(Integer, default=0)

    hero_image: Mapped[Image | None] = relationship(Image, lazy="joined")
    tags: Mapped[list[Tag]] = relationship(
        Tag, secondary=RecipeTag.__table__, lazy="selectin"
    )


class Redirect(Base):
    __tablename__ = "redirects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    old_path: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    new_path: Mapped[str] = mapped_column(String(300))


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class DailyView(Base):
    __tablename__ = "daily_views"
    __table_args__ = (
        UniqueConstraint("content_type", "content_id", "date", name="uq_daily_view"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_type: Mapped[str] = mapped_column(String(10))  # "post" | "recipe"
    content_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    count: Mapped[int] = mapped_column(Integer, default=0)
