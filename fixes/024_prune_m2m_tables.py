# FIXES/022_SET_STATUS_ON_DUPLICATE_ERROR_SUBSCRIPTION_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys

# ## EXTERNAL IMPORTS
from sqlalchemy import text


# ## GLOBAL VARIABLES

PRUNE_ARTIST_PROFILES_DUPLICATES = """
DELETE
FROM artist_profiles
WHERE (artist_profiles.artist_id, artist_profiles.description_id) IN (
SELECT artist_profiles.artist_id, description_bodies.description_id
FROM artist_profiles
JOIN description ON description.id = artist_profiles.description_id
JOIN
	(SELECT description.id AS description_id, description.body, ROW_NUMBER() OVER (PARTITION BY description.body) AS rn
	FROM description) AS description_bodies ON description_bodies.body = description.body
WHERE description_bodies.rn > 1)
"""

PRUNE_ILLUST_COMMENTARIES_DUPLICATES = """
DELETE
FROM illust_commentaries
WHERE (illust_commentaries.illust_id, illust_commentaries.description_id) IN (
SELECT illust_commentaries.illust_id, description_bodies.description_id
FROM illust_commentaries
JOIN description ON description.id = illust_commentaries.description_id
JOIN
	(SELECT description.id AS description_id, description.body, ROW_NUMBER() OVER (PARTITION BY description.body) AS rn
	FROM description) AS description_bodies ON description_bodies.body = description.body
WHERE description_bodies.rn > 1);
"""

PRUNE_ARTIST_SITE_ACCOUNTS_DUPLICATES = """
DELETE
FROM artist_site_accounts
WHERE (artist_site_accounts.artist_id, artist_site_accounts.label_id) IN (
SELECT artist_site_accounts.artist_id, label_names.label_id
FROM artist_site_accounts
JOIN label ON label.id = artist_site_accounts.label_id
JOIN
	(SELECT label.id AS label_id, label.name, ROW_NUMBER() OVER (PARTITION BY label.name) AS rn
	FROM label) AS label_names ON label_names.name = label.name
WHERE label_names.rn > 1);
"""

PRUNE_ARTIST_NAMES_DUPLICATES = """
DELETE
FROM artist_names
WHERE (artist_names.artist_id, artist_names.label_id) IN (
SELECT artist_names.artist_id, label_names.label_id
FROM artist_names
JOIN label ON label.id = artist_names.label_id
JOIN
	(SELECT label.id AS label_id, label.name, ROW_NUMBER() OVER (PARTITION BY label.name) AS rn
	FROM label) AS label_names ON label_names.name = label.name
WHERE label_names.rn > 1);
"""

PRUNE_BOORU_NAMES_DUPLICATES = """
DELETE
FROM booru_names
WHERE (booru_names.booru_id, booru_names.label_id) IN (
SELECT booru_names.booru_id, label_names.label_id
FROM booru_names
JOIN label ON label.id = booru_names.label_id
JOIN
	(SELECT label.id AS label_id, label.name, ROW_NUMBER() OVER (PARTITION BY label.name) AS rn
	FROM label) AS label_names ON label_names.name = label.name
WHERE label_names.rn > 1);
"""

PRUNE_UNUSED_DESCRIPTIONS = """
DELETE FROM description
WHERE description.id NOT IN (
	SELECT illust_commentaries.description_id
	FROM illust_commentaries
	UNION ALL
	SELECT artist_profiles.description_id
	FROM artist_profiles
)
"""

PRUNE_UNUSED_LABELS = """
DELETE FROM label
WHERE label.id NOT IN (
	SELECT artist_site_accounts.label_id
	FROM artist_site_accounts
	UNION ALL
	SELECT artist_names.label_id
	FROM artist_names
	UNION ALL
	SELECT booru_names.label_id
	FROM booru_names
)
"""


# ## FUNCTIONS

# #### Auxiliary functions

def initialize():
    global SESSION
    os.environ['USE_ENUMS'] = 'false'
    sys.path.append(os.path.abspath('.'))
    from app import SESSION


# #### Main execution functions

def main():
    # THIS SHOULD ONLY BE RUN BEFORE RUNNING THE MIGRATIONS of 2.36
    initialize()

    print("Pruning artist profiles")
    SESSION.execute(text(PRUNE_ARTIST_PROFILES_DUPLICATES))
    SESSION.commit()

    print("Pruning illust commentaries")
    SESSION.execute(text(PRUNE_ILLUST_COMMENTARIES_DUPLICATES))
    SESSION.commit()

    print("Pruning artist site accounts")
    SESSION.execute(text(PRUNE_ARTIST_SITE_ACCOUNTS_DUPLICATES))
    SESSION.commit()

    print("Pruning artist names")
    SESSION.execute(text(PRUNE_ARTIST_NAMES_DUPLICATES))
    SESSION.commit()

    print("Pruning booru names")
    SESSION.execute(text(PRUNE_BOORU_NAMES_DUPLICATES))
    SESSION.commit()

    print("Pruning descriptions")
    SESSION.execute(text(PRUNE_UNUSED_DESCRIPTIONS))
    SESSION.commit()

    print("Pruning labels")
    SESSION.execute(text(PRUNE_UNUSED_LABELS))
    SESSION.commit()


# ##EXECUTION START

if __name__ == '__main__':
    main()
