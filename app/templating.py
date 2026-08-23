from fastapi.templating import Jinja2Templates

from app.config import ASSET_VERSION, SITE_NAME, TAGLINE, TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals.update(
    site_name=SITE_NAME,
    tagline=TAGLINE,
    asset_v=ASSET_VERSION,
)
