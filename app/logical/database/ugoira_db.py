# APP/LOGICAL/DATABASE/UGOIRA_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import Ugoira, Post, IllustUrl
from .base_db import remove_duplicate_items, prune_unused_items


# ## GLOBAL VARIABLES

UGOIRA_UNION_CLAUSE = union_all(
    Post.query.filter(Post.ugoira_id.is_not(None)).with_entities(Post.ugoira_id),
    IllustUrl.query.filter(IllustUrl.ugoira_id.is_not(None)).with_entities(IllustUrl.ugoira_id),
)

UGOIRA_FOREIGN_KEYS = [
    (Post, Post.ugoira_id),
    (IllustUrl, IllustUrl.ugoira_id),
]


# ## FUNCTIONS

def remove_duplicate_ugoiras():
    return remove_duplicate_items(Ugoira, Ugoira.frames, UGOIRA_FOREIGN_KEYS)


def prune_unused_ugoiras():
    return prune_unused_items(Ugoira, UGOIRA_UNION_CLAUSE)
