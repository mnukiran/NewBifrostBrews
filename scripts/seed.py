"""Seed the database with sample mead-themed content for local development."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import ContentStatus, Difficulty, Post, Recipe, Setting, Tag
from app.services.content import rebuild_search_index_row
from app.services.markdown import reading_minutes, render_markdown

SAMPLE_NOTE = "\n\n*This is placeholder sample content added during setup.*"

TAGS = [
    ("Traditional", "traditional"),
    ("Beginner Tips", "beginner-tips"),
    ("Ingredients", "ingredients"),
    ("Cyser", "cyser"),
    ("Sample Content", "sample-content"),
]

ARTICLES = [
    {
        "title": "Choosing the Right Honey for Your First Mead",
        "slug": "choosing-the-right-honey-for-your-first-mead",
        "summary": "Not all honey is created equal. Here's what to look for when picking a honey for your first batch.",
        "tags": ["beginner-tips", "ingredients", "sample-content"],
        "days_ago": 12,
        "body_md": (
            "Honey is the single largest ingredient in any mead, so its character "
            "shapes the final drink more than any other choice you'll make.\n\n"
            "## Raw vs. filtered\n\n"
            "Raw honey retains trace pollen, wax, and wild yeast that can add "
            "complexity -- but it also ferments a little less predictably than "
            "filtered honey. For a first batch, a light filtered wildflower honey "
            "gives you a clean, forgiving base.\n\n"
            "## Varietal character\n\n"
            "Clover and wildflower honeys are mild and floral. Buckwheat and "
            "chestnut honeys are dark, malty, and assertive -- wonderful in a "
            "braggot, overpowering in a delicate traditional mead.\n\n"
            "## A simple rule\n\n"
            "If you can't decide, start with a mild wildflower honey. It will "
            "let the yeast and fermentation character speak clearly, and you'll "
            "have a much easier time diagnosing off-flavors if something goes "
            "wrong." + SAMPLE_NOTE
        ),
    },
    {
        "title": "Understanding Gravity Readings: OG, FG, and ABV Explained",
        "slug": "understanding-gravity-readings-og-fg-abv",
        "summary": "A short, practical guide to what your hydrometer is actually telling you.",
        "tags": ["beginner-tips", "sample-content"],
        "days_ago": 6,
        "body_md": (
            "Every mead recipe on this site lists an OG and FG. Here's what "
            "those numbers mean and why they matter.\n\n"
            "## Original Gravity (OG)\n\n"
            "OG is a measure of dissolved sugar in your must before "
            "fermentation starts. A higher OG means more sugar for the yeast to "
            "convert -- and generally a stronger, sweeter starting point.\n\n"
            "## Final Gravity (FG)\n\n"
            "FG is the same measurement taken once fermentation has finished. "
            "The gap between OG and FG tells you how much sugar the yeast "
            "actually consumed.\n\n"
            "## Estimating ABV\n\n"
            "A common approximation is:\n\n"
            "```\n"
            "ABV = (OG - FG) * 131.25\n"
            "```\n\n"
            "It isn't perfectly precise, but it's close enough to plan a "
            "recipe and to sanity-check your fermentation." + SAMPLE_NOTE
        ),
    },
    {
        "title": "Why Patience Is the Secret Ingredient in Mead-Making",
        "slug": "why-patience-is-the-secret-ingredient",
        "summary": "Mead rewards waiting more than almost any other homebrew. Here's why it's worth it.",
        "tags": ["traditional", "sample-content"],
        "days_ago": 2,
        "body_md": (
            "Beer is often ready in weeks. Mead, done well, asks for months -- "
            "sometimes longer.\n\n"
            "## Fermentation is only the beginning\n\n"
            "Primary fermentation might wrap up in two to four weeks, but the "
            "harsh, yeasty edges of a young mead need time in secondary to "
            "settle and round out.\n\n"
            "## Aging changes everything\n\n"
            "A traditional mead tasted at bottling can seem thin or hot with "
            "alcohol. The same mead, six months later, is often unrecognizable "
            "-- smoother, rounder, and with the honey character finally able "
            "to shine through.\n\n"
            "> The best time to bottle a mead is usually later than you think."
            + SAMPLE_NOTE
        ),
    },
]

RECIPES = [
    {
        "title": "Traditional Wildflower Mead",
        "slug": "traditional-wildflower-mead",
        "summary": "A classic, no-frills traditional mead that lets wildflower honey take center stage.",
        "tags": ["traditional", "sample-content"],
        "days_ago": 20,
        "style": "traditional",
        "batch_liters": 4.0,
        "og": 1.110,
        "fg": 1.010,
        "difficulty": Difficulty.beginner,
        "ingredients": [
            {"amount": "1.5", "unit": "kg", "item": "Wildflower honey"},
            {"amount": "3.2", "unit": "L", "item": "Filtered water"},
            {"amount": "1", "unit": "pack", "item": "Lalvin 71B-1122 yeast"},
            {"amount": "2.5", "unit": "g", "item": "Fermaid-O yeast nutrient", "note": "split into 3 additions"},
        ],
        "steps": [
            {"day_offset": 0, "title": "Brew Day", "description": "Warm honey into water off-heat, pitch rehydrated yeast at room temperature."},
            {"day_offset": 2, "title": "First Nutrient Addition", "description": "Degas and add the first third of nutrient."},
            {"day_offset": 5, "title": "Second Nutrient Addition", "description": "Degas and add the second third of nutrient."},
            {"day_offset": 10, "title": "Check Gravity", "description": "Fermentation should be slowing; take a gravity reading."},
            {"day_offset": 30, "title": "Rack to Secondary", "description": "Once gravity is stable, rack off the lees into a clean vessel."},
            {"day_offset": 180, "title": "Bottle", "description": "Bottle and age at least another 3 months before drinking."},
        ],
        "body_md": (
            "This is the mead I recommend to anyone brewing their first batch. "
            "No fruit, no spice -- just honey, water, and yeast, so any mistakes "
            "(or successes) are easy to learn from." + SAMPLE_NOTE
        ),
    },
    {
        "title": "Spiced Apple Cyser",
        "slug": "spiced-apple-cyser",
        "summary": "A cider-mead hybrid warmed with cinnamon and clove -- perfect for autumn.",
        "tags": ["cyser", "sample-content"],
        "days_ago": 9,
        "style": "cyser",
        "batch_liters": 4.0,
        "og": 1.095,
        "fg": 1.005,
        "difficulty": Difficulty.intermediate,
        "ingredients": [
            {"amount": "1.1", "unit": "kg", "item": "Clover honey"},
            {"amount": "3.5", "unit": "L", "item": "Fresh-pressed apple juice", "note": "no preservatives"},
            {"amount": "1", "unit": "pack", "item": "Lalvin D47 yeast"},
            {"amount": "2", "unit": "sticks", "item": "Cinnamon"},
            {"amount": "4", "unit": "whole", "item": "Cloves"},
        ],
        "steps": [
            {"day_offset": 0, "title": "Brew Day", "description": "Blend honey into juice, pitch yeast; add cinnamon and clove in a hop bag."},
            {"day_offset": 5, "title": "Remove Spices", "description": "Pull the spice bag to keep the spicing balanced, not overpowering."},
            {"day_offset": 14, "title": "Check Gravity", "description": "Fermentation should be nearly finished; take a reading."},
            {"day_offset": 28, "title": "Rack to Secondary", "description": "Rack off the lees once gravity is stable across two readings."},
            {"day_offset": 120, "title": "Bottle", "description": "Bottle and let mellow at least 6-8 weeks before serving."},
        ],
        "body_md": (
            "A great gateway mead for cider drinkers -- the apple juice keeps "
            "things bright while the honey adds body the spices can lean on."
            + SAMPLE_NOTE
        ),
    },
]

ABOUT_MD = (
    "# About Bifrost Brews\n\n"
    "Bifrost Brews is a small, hand-kept record of mead-making experiments -- "
    "recipes, notes on what worked, and the occasional batch that didn't.\n\n"
    "*(Sample About page content -- edit me from the admin panel.)*"
)


def get_or_create_tag(db, name: str, slug: str) -> Tag:
    tag = db.query(Tag).filter_by(slug=slug).first()
    if tag:
        return tag
    tag = Tag(name=name, slug=slug)
    db.add(tag)
    db.flush()
    return tag


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Post).count() or db.query(Recipe).count():
            print("Database already has content -- skipping seed.")
            return

        tag_by_slug = {slug: get_or_create_tag(db, name, slug) for name, slug in TAGS}

        now = datetime.utcnow()

        for article in ARTICLES:
            body_html = render_markdown(article["body_md"])
            post = Post(
                title=article["title"],
                slug=article["slug"],
                summary=article["summary"],
                body_md=article["body_md"],
                body_html=body_html,
                status=ContentStatus.published,
                published_at=now - timedelta(days=article["days_ago"]),
                reading_minutes=reading_minutes(article["body_md"]),
                view_count=0,
                tags=[tag_by_slug[slug] for slug in article["tags"]],
            )
            db.add(post)
            db.flush()
            rebuild_search_index_row(
                db, "post", post.id, post.title, post.summary, post.body_md
            )

        for recipe in RECIPES:
            abv = round((recipe["og"] - recipe["fg"]) * 131.25, 2)
            total_days = max(step["day_offset"] for step in recipe["steps"])
            body_html = render_markdown(recipe["body_md"])
            rec = Recipe(
                title=recipe["title"],
                slug=recipe["slug"],
                summary=recipe["summary"],
                body_md=recipe["body_md"],
                body_html=body_html,
                status=ContentStatus.published,
                published_at=now - timedelta(days=recipe["days_ago"]),
                reading_minutes=reading_minutes(recipe["body_md"]),
                view_count=0,
                style=recipe["style"],
                batch_liters=recipe["batch_liters"],
                og=recipe["og"],
                fg=recipe["fg"],
                abv=abv,
                difficulty=recipe["difficulty"],
                ingredients_json=recipe["ingredients"],
                steps_json=recipe["steps"],
                total_days=total_days,
                tags=[tag_by_slug[slug] for slug in recipe["tags"]],
            )
            db.add(rec)
            db.flush()
            rebuild_search_index_row(
                db, "recipe", rec.id, rec.title, rec.summary, rec.body_md
            )

        db.merge(Setting(key="about_md", value=ABOUT_MD))
        db.merge(Setting(key="about_html", value=render_markdown(ABOUT_MD)))
        db.merge(Setting(key="site_tagline", value="Nectar of the Gods"))

        db.commit()
        print(
            f"Seeded {len(ARTICLES)} articles, {len(RECIPES)} recipes, "
            f"{len(TAGS)} tags."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
