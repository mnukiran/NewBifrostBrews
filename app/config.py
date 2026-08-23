import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

DB_PATH = Path(os.environ.get("BIFROST_DB", BASE_DIR.parent / "db" / "bifrost.db"))

SITE_NAME = "Bifrost Brews"
TAGLINE = "Learn AI. Brew conversation."

# If set, signing up requires this code (share it with coworkers).
# Empty = open signup — fine on LAN, set a code before exposing the site.
INVITE_CODE = os.environ.get("BIFROST_INVITE_CODE", "").strip()

# Bump when static assets change so far-future-cached clients refetch.
ASSET_VERSION = "4"
