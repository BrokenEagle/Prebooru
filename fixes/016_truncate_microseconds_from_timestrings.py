# FIXES/016_TRUNCATE_MICROSECONDS_FROM_TIMESTRINGS.PY

# ## PYTHON IMPORTS
import os
import sys
import datetime
from argparse import ArgumentParser
from dateutil.relativedelta import relativedelta


# ## GLOBAL VARIABLES

TIME_OFFSET = relativedelta(years=1000)


# ## FUNCTIONS

def initialize():
    global SESSION, TABLES, NormalizedDatetime
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import TABLES
    from app.models.base import NormalizedDatetime


def datetime_model_iterator():
    for name in TABLES:
        model = TABLES[name]
        if not hasattr(model, 'basic_attributes'):
            continue
        has_datetime = False
        for attribute in model.basic_attributes:
            if isinstance(getattr(model.__table__.c, attribute).type, NormalizedDatetime):
                has_datetime = True
                break
        if not has_datetime:
            continue
        print("Processing:", model._model_name())
        yield model


def second_pass():
    for model in datetime_model_iterator():
        for item in model.query.all():
            updated_attributes = []
            for attribute in item.basic_attributes:
                value = getattr(item, attribute)
                if not isinstance(value, datetime.datetime):
                    continue
                if value > datetime.datetime(2000, 1, 1):
                    continue
                updated_value = value + TIME_OFFSET
                setattr(item, attribute, updated_value)
                updated_attributes.append(attribute)
            if len(updated_attributes):
                print("\tUpdated", item.shortlink, '->', updated_attributes)
        SESSION.commit()


def first_pass():
    for model in datetime_model_iterator():
        for item in model.query.all():
            updated_attributes = []
            for attribute in item.basic_attributes:
                value = getattr(item, attribute)
                if not isinstance(value, datetime.datetime):
                    continue
                if value < datetime.datetime(2000, 1, 1):
                    continue
                updated_value = value - TIME_OFFSET
                setattr(item, attribute, updated_value)
                updated_attributes.append(attribute)
            if len(updated_attributes):
                print("\tUpdated", item.shortlink, '->', updated_attributes)
        SESSION.commit()


def main(args):
    if args.type in ['both', 'first']:
        first_pass()
    if args.type in ['both', 'second']:
        second_pass()

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to rewrite all timestrings with DB with microseconds truncated.")
    parser.add_argument('type', choices=['both', 'first', 'second'],
                        help="Choose which step to perform.")
    args = parser.parse_args()

    initialize()
    main(args)
