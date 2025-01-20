# APP/LOGICAL/DATABASE/LABEL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import Label, ArtistNames, ArtistSiteAccounts, BooruNames
from .base_db import commit_session


# ## GLOBAL VARIABLES

LABEL_UNION_CLAUSE = union_all(
    ArtistNames.query.with_entities(ArtistNames.label_id),
    ArtistSiteAccounts.query.with_entities(ArtistSiteAccounts.label_id),
    BooruNames.query.with_entities(BooruNames.label_id),
)


# ## FUNCTIONS

def prune_unused_labels():
    delete_count = Label.query.filter(Label.id.not_in(LABEL_UNION_CLAUSE))\
                              .delete(synchronize_session=False)
    commit_session()
    return delete_count
