"""fts5 search index

Revision ID: a2261d5ae847
Revises: c8262e520049
Create Date: 2026-07-06 21:06:05.040578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2261d5ae847'
down_revision: Union[str, None] = 'c8262e520049'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIRTUAL TABLE search_index USING fts5(
            content_type UNINDEXED,
            content_id UNINDEXED,
            title,
            summary,
            body_text
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE search_index")
