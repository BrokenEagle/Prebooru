from app.models import Illust
from utility.file import put_get_raw

OUTPUT_FILE = r'C:\Users\Justin\GitHub\ai_setup\misc\insert_illust_tags.sql'

INSERT_STATEMENT = """
REPLACE INTO tag(id, name, type_id)
VALUES
(100000, 'to_delete', 1);
INSERT INTO ILLUST_TAGS(illust_id, tag_id)
VALUES
%s;
"""

def output_sql():
    illusts = Illust.query.filter(Illust.id <= 267452).all()
    values = ["(%d, 100000)" % illust.id for illust in illusts]
    output = INSERT_STATEMENT % ',\n'.join(values)
    put_get_raw(OUTPUT_FILE, 'w', output.strip())

output_sql()
