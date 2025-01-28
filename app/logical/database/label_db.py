# APP/LOGICAL/DATABASE/LABEL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all, func

# ## LOCAL IMPORTS
from ...models import Label, Artist, Booru, ArtistNames, ArtistSiteAccounts, BooruNames
from .base_db import commit_session, flush_session, delete_record


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
    duplicates = Label.query.group_by(Label.name)\
                            .having(func.count(Label.name) > 1)\
                            .with_entities(Label.name)\
                            .all()
    total = len(duplicates)
    if total == 0:
        return total
    for duplicate in duplicates:
        labels = Label.query.filter_by(name=duplicate[0]).all()
        update_id = labels[0].id
        # Remove duplicates in M2M beore updating, otherwise it could violate the unique constraint
        for foreign_key in LABEL_FOREIGN_KEYS:
            if not foreign_key[0]._secondary_table:
                continue
            model, attach_column, primary_id = foreign_key
            attach_id = attach_column.name
            primary_column = getattr(model, primary_id)
            items = model.query.filter(attach_column.in_(label.id for label in labels)).all()
            seen_primary_ids = set()
            for item in items:
                if item[primary_id] in seen_primary_ids:
                    model.query.filter(primary_column == item[primary_id], attach_column == item[attach_id]).delete()
                    flush_session()
                else:
                    seen_primary_ids.add(item[primary_id])
        # Update tables to the first label found
        for label in labels[1:]:
            for foreign_key in LABEL_FOREIGN_KEYS:
                model, attach_column, *_ = foreign_key
                model.query.filter(attach_column == label.id).update({attach_column.name: update_id})
                flush_session()
            delete_record(label)
            flush_session()
    commit_session()
    return total


def prune_unused_labels():
    delete_count = Label.query.filter(Label.id.not_in(LABEL_UNION_CLAUSE))\
                              .delete(synchronize_session=False)
    commit_session()
    return delete_count
