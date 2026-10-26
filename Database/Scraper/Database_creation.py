import httpx
import os
from datetime import datetime, timezone
from datetime import datetime
import time
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint, create_engine, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.dialects.postgresql import insert


class Base(DeclarativeBase):
    pass


class Language(Base):
    __tablename__ = "Language"

    language_surr_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    language_code: Mapped[str | None] = mapped_column(Text, unique=True)
    language_name: Mapped[str | None] = mapped_column(Text)


class Source(Base):
    __tablename__ = "Source"

    source_surr_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    source_name: Mapped[str | None] = mapped_column(Text, unique=True)
    source_rank: Mapped[int | None] = mapped_column(SmallInteger)


class Tag(Base):
    __tablename__ = "Tag"

    tag_surr_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    tag_name: Mapped[str | None] = mapped_column(Text, unique=True)
    tag_description: Mapped[str | None] = mapped_column(Text)
    is_adult: Mapped[bool | None] = mapped_column(Boolean)


class Creators(Base):
    __tablename__ = "Creators"

    creator_surr_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creator_name: Mapped[str | None] = mapped_column(Text)
    creator_anilist_id: Mapped[str | None] = mapped_column(Text, unique=True)


class Manga(Base):
    __tablename__ = "Manga"

    manga_surr_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manga_release_year: Mapped[int | None] = mapped_column(Integer)
    manga_description: Mapped[str | None] = mapped_column(Text)
    anilist_id: Mapped[str | None] = mapped_column(Text, unique=True)
    # my_anime_list_id: Mapped[str | None] = mapped_column(Text, unique=True)
    is_completed: Mapped[bool | None] = mapped_column(Boolean)
    is_adult: Mapped[bool | None] = mapped_column(Boolean)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manga_original_language_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("Language.language_surr_id")
    )


class Title(Base):
    __tablename__ = "Title"

    title_surr_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manga_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("Manga.manga_surr_id")
    )
    title_name: Mapped[str | None] = mapped_column(Text)
    is_prime: Mapped[bool | None] = mapped_column(Boolean)

    __table_args__ = (
        UniqueConstraint("manga_id", "title_name", name="uq_manga_title"),
    )


class Cover(Base):
    __tablename__ = "Cover"

    manga_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Manga.manga_surr_id"), primary_key=True
    )
    src_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("Source.source_surr_id"), primary_key=True
    )
    volume: Mapped[str | None] = mapped_column(Text, primary_key=True)
    cover_src_id: Mapped[str | None] = mapped_column(Text)
    cover_location: Mapped[str | None] = mapped_column(Text)
    cover_link: Mapped[str | None] = mapped_column(Text)


class Chapter(Base):
    __tablename__ = "Chapter"

    chapter_surr_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    manga_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("Manga.manga_surr_id")
    )
    chapter_number: Mapped[float | None] = mapped_column(Numeric(8, 2))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chapter_title: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("manga_id", "chapter_number", name="uq_manga_chapter_number"),
    )


class MangaTag(Base):
    __tablename__ = "MangaTag"

    manga_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Manga.manga_surr_id"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("Tag.tag_surr_id"), primary_key=True
    )



class MangaSources(Base):
    __tablename__ = "Manga_Sources"

    manga_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Manga.manga_surr_id"), primary_key=True
    )
    src_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("Source.source_surr_id"), primary_key=True
    )
    manga_src_id: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manga_link: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("src_id", "manga_src_id", name="uq_source_manga_src_id"),
    )


class ChapterSources(Base):
    __tablename__ = "Chapter_Sources"

    chapter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("Chapter.chapter_surr_id"), primary_key=True
    )
    src_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("Source.source_surr_id"), primary_key=True
    )
    chapter_src_id: Mapped[str | None] = mapped_column(Text)
    chapter_location: Mapped[str | None] = mapped_column(Text)
    chapter_link: Mapped[str | None] = mapped_column(Text)
    pages_count: Mapped[int | None] = mapped_column(SmallInteger)
    is_downloaded: Mapped[bool | None] = mapped_column(Boolean)

    __table_args__ = (
        UniqueConstraint("src_id", "chapter_src_id", name="uq_source_chapter_src_id"),
    )


class MangaCreators(Base):
    __tablename__ = "Manga_Creators"

    manga_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Manga.manga_surr_id"), primary_key=True
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Creators.creator_surr_id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(Text, primary_key=True)

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created successfully.")










