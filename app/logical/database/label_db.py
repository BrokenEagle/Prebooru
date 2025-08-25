# APP/LOGICAL/DATABASE/LABEL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import Label, Artist, Booru, ArtistNames, ArtistSiteAccounts, BooruNames
from .base_db import remove_duplicate_items, prune_unused_items


# ## GLOBAL VARIABLES

LABEL_UNION_CLAUSE = union_all(
    Artist.query.with_entities(Artist.site_account_id),
    Artist.query.filter(Artist.name_id.is_not(None)).with_entities(Artist.name_id),
    ArtistNames.query.with_entities(ArtistNames.label_id),
    ArtistSiteAccounts.query.with_entities(ArtistSiteAccounts.label_id),
    Booru.query.filter(Booru.name_id.is_not(None)).with_entities(Booru.name_id),
    BooruNames.query.with_entities(BooruNames.label_id),
)

LABEL_FOREIGN_KEYS = [
    (Artist, Artist.site_account_id),
    (Artist, Artist.name_id),
    (ArtistSiteAccounts, ArtistSiteAccounts.label_id, 'artist_id'),
    (ArtistNames, ArtistNames.label_id, 'artist_id'),
    (Booru, Booru.name_id),
    (BooruNames, BooruNames.label_id, 'booru_id'),
]


# ## FUNCTIONS

def remove_duplicate_labels():
    return remove_duplicate_items(Label, Label.name, LABEL_FOREIGN_KEYS)


def prune_unused_labels():
    return prune_unused_items(Label, LABEL_UNION_CLAUSE)
