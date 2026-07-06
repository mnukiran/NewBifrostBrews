from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, select, text
from sqlalchemy.orm import Session

from app.models import ContentStatus, DailyView, Post, Recipe, Tag

ARTICLES_PER_PAGE = 12
RECIPES_PER_PAGE = 12


def published_clause(model):
    return and_(
        model.status != ContentStatus.draft,
        model.published_at.is_not(None),
        model.published_at <= datetime.utcnow(),
    )


@dataclass
class Page:
    items: list
    page: int
    per_page: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.per_page))

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages


def get_home_data(db: Session) -> dict:
    latest_recipes = db.scalars(
        select(Recipe)
        .where(published_clause(Recipe))
        .order_by(Recipe.published_at.desc())
        .limit(3)
    ).all()
    latest_posts = db.scalars(
        select(Post)
        .where(published_clause(Post))
        .order_by(Post.published_at.desc())
        .limit(5)
    ).all()
    tags = db.scalars(select(Tag).order_by(Tag.name)).all()
    return {
        "latest_recipes": latest_recipes,
        "latest_posts": latest_posts,
        "tags": tags,
    }


def list_articles(db: Session, page: int = 1) -> Page:
    base = select(Post).where(published_clause(Post))
    total = db.scalar(select(text("count(*)")).select_from(base.subquery()))
    items = db.scalars(
        base.order_by(Post.published_at.desc())
        .limit(ARTICLES_PER_PAGE)
        .offset((page - 1) * ARTICLES_PER_PAGE)
    ).all()
    return Page(items=items, page=page, per_page=ARTICLES_PER_PAGE, total=total)


def get_article_by_slug(db: Session, slug: str) -> Post | None:
    return db.scalar(
        select(Post).where(Post.slug == slug, published_clause(Post))
    )


def list_recipes(
    db: Session,
    page: int = 1,
    style: str | None = None,
    difficulty: str | None = None,
    tag_slug: str | None = None,
) -> Page:
    base = select(Recipe).where(published_clause(Recipe))
    if style:
        base = base.where(Recipe.style == style)
    if difficulty:
        base = base.where(Recipe.difficulty == difficulty)
    if tag_slug:
        base = base.join(Recipe.tags).where(Tag.slug == tag_slug)
    total = db.scalar(select(text("count(*)")).select_from(base.subquery()))
    items = db.scalars(
        base.order_by(Recipe.published_at.desc())
        .limit(RECIPES_PER_PAGE)
        .offset((page - 1) * RECIPES_PER_PAGE)
    ).all()
    return Page(items=items, page=page, per_page=RECIPES_PER_PAGE, total=total)


def get_recipe_by_slug(db: Session, slug: str) -> Recipe | None:
    return db.scalar(
        select(Recipe).where(Recipe.slug == slug, published_clause(Recipe))
    )


def get_tag_by_slug(db: Session, slug: str) -> Tag | None:
    return db.scalar(select(Tag).where(Tag.slug == slug))


def content_for_tag(db: Session, tag: Tag) -> list:
    posts = db.scalars(
        select(Post)
        .join(Post.tags)
        .where(Tag.id == tag.id, published_clause(Post))
    ).all()
    recipes = db.scalars(
        select(Recipe)
        .join(Recipe.tags)
        .where(Tag.id == tag.id, published_clause(Recipe))
    ).all()
    combined = list(posts) + list(recipes)
    combined.sort(key=lambda item: item.published_at, reverse=True)
    return combined


def related_posts_by_tag(db: Session, post: Post, limit: int = 3) -> list[Post]:
    if not post.tags:
        return []
    tag_ids = [tag.id for tag in post.tags]
    return db.scalars(
        select(Post)
        .join(Post.tags)
        .where(
            Tag.id.in_(tag_ids),
            Post.id != post.id,
            published_clause(Post),
        )
        .order_by(Post.published_at.desc())
        .limit(limit)
    ).all()


def record_view(db: Session, content_type: str, item: Post | Recipe) -> None:
    item.view_count += 1
    today = datetime.utcnow().strftime("%Y-%m-%d")
    row = db.scalar(
        select(DailyView).where(
            DailyView.content_type == content_type,
            DailyView.content_id == item.id,
            DailyView.date == today,
        )
    )
    if row:
        row.count += 1
    else:
        db.add(
            DailyView(content_type=content_type, content_id=item.id, date=today, count=1)
        )
    db.commit()


def rebuild_search_index_row(
    db: Session,
    content_type: str,
    content_id: int,
    title: str,
    summary: str,
    body_text: str,
) -> None:
    db.execute(
        text(
            "DELETE FROM search_index WHERE content_type = :ct AND content_id = :ci"
        ),
        {"ct": content_type, "ci": content_id},
    )
    db.execute(
        text(
            "INSERT INTO search_index (content_type, content_id, title, summary, body_text) "
            "VALUES (:ct, :ci, :title, :summary, :body)"
        ),
        {
            "ct": content_type,
            "ci": content_id,
            "title": title,
            "summary": summary,
            "body": body_text,
        },
    )


@dataclass
class SearchResult:
    content_type: str
    content_id: int
    title: str
    snippet: str
    slug: str
    published_at: datetime


def search(db: Session, query: str, limit: int = 20) -> list[SearchResult]:
    if not query.strip():
        return []
    rows = db.execute(
        text(
            """
            SELECT content_type, content_id, title,
                   snippet(search_index, 4, '<mark>', '</mark>', '...', 24) AS snip
            FROM search_index
            WHERE search_index MATCH :query
            ORDER BY bm25(search_index)
            LIMIT :limit
            """
        ),
        {"query": query, "limit": limit},
    ).all()

    results: list[SearchResult] = []
    for content_type, content_id, title, snip in rows:
        model = Post if content_type == "post" else Recipe
        item = db.get(model, content_id)
        if item is None or item.status == ContentStatus.draft:
            continue
        results.append(
            SearchResult(
                content_type=content_type,
                content_id=content_id,
                title=title,
                snippet=snip,
                slug=item.slug,
                published_at=item.published_at,
            )
        )
    return results
