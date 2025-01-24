# APP/LOGICAL/DATABASE/LABEL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import Label, Artist, Booru, ArtistNames, ArtistSiteAccounts, BooruNames
from .base_db import commit_session


# ## GLOBAL VARIABLES

LABEL_UNION_CLAUSE = union_all(
    Artist.query.with_entities(Artist.site_account_id),
    Artist.query.filter(Artist.name_id.is_not(None)).with_entities(Artist.name_id),
    ArtistNames.query.with_entities(ArtistNames.label_id),
    ArtistSiteAccounts.query.with_entities(ArtistSiteAccounts.label_id),
    Booru.query.filter(Booru.name_id.is_not(None)).with_entities(Booru.name_id),
    BooruNames.query.with_entities(BooruNames.label_id),
)


# ## FUNCTIONS

def prune_unused_labels():
    delete_count = Label.query.filter(Label.id.not_in(LABEL_UNION_CLAUSE))\
                              .delete(synchronize_session=False)
    commit_session()
    return delete_count
