# APP/LOGICAL/DATABASE/DESCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all, func

# ## LOCAL IMPORTS
from ...models import Description, Artist, Illust, IllustTitles, IllustCommentaries, AdditionalCommentaries,\
    ArtistProfiles
from .base_db import commit_session, flush_session, delete_record


# ## GLOBAL VARIABLES

DESCRIPTION_UNION_CLAUSE = union_all(
    Illust.query.filter(Illust.title_id.is_not(None)).with_entities(Illust.title_id),
    Illust.query.filter(Illust.commentary_id.is_not(None)).with_entities(Illust.commentary_id),
    IllustTitles.query.with_entities(IllustTitles.description_id),
    IllustCommentaries.query.with_entities(IllustCommentaries.description_id),
    AdditionalCommentaries.query.with_entities(AdditionalCommentaries.description_id),
    Artist.query.filter(Artist.profile_id.is_not(None)).with_entities(Artist.profile_id),
    ArtistProfiles.query.with_entities(ArtistProfiles.description_id)
)

DESCRIPTION_FOREIGN_KEYS = [
    (Illust, Illust.title_id),
    (Illust, Illust.commentary_id),
    (IllustTitles, IllustTitles.description_id, 'illust_id'),
    (IllustCommentaries, IllustCommentaries.description_id, 'illust_id'),
    (AdditionalCommentaries, AdditionalCommentaries.description_id, 'illust_id'),
    (Artist, Artist.profile_id),
    (ArtistProfiles, ArtistProfiles.description_id, 'artist_id'),
]


# ## FUNCTIONS

def remove_duplicate_descriptions():
    duplicates = Description.query.group_by(Description.body)\
                                  .having(func.count(Description.body) > 1)\
                                  .with_entities(Description.body)\
                                  .all()
    total = len(duplicates)
    if total == 0:
        return total
    for duplicate in duplicates:
        descriptions = Description.query.filter_by(body=duplicate[0]).all()
        update_id = descriptions[0].id
        # Remove duplicates in M2M beore updating, otherwise it could violate the unique constraint
        for foreign_key in DESCRIPTION_FOREIGN_KEYS:
            if not foreign_key[0]._secondary_table:
                continue
            model, attach_column, primary_id = foreign_key
            attach_id = attach_column.name
            primary_column = getattr(model, primary_id)
            items = model.query.filter(attach_column.in_(description.id for description in descriptions)).all()
            seen_primary_ids = set()
            for item in items:
                if item[primary_id] in seen_primary_ids:
                    model.query.filter(primary_column == item[primary_id], attach_column == item[attach_id]).delete()
                    flush_session()
                else:
                    seen_primary_ids.add(item[primary_id])
        # Update tables to the first description found
        for description in descriptions[1:]:
            for foreign_key in DESCRIPTION_FOREIGN_KEYS:
                model, attach_column, *_ = foreign_key
                model.query.filter(attach_column == description.id).update({attach_column.name: update_id})
                flush_session()
            delete_record(description)
            flush_session()
    commit_session()
    return total


def prune_unused_descriptions():
    delete_count = Description.query.filter(Description.id.not_in(DESCRIPTION_UNION_CLAUSE))\
                                    .delete(synchronize_session=False)
    commit_session()
    return delete_count
