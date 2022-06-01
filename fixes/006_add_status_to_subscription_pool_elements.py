# FIXES/001_ADD_STATUS_TO_SUBSCRIPTION_POOL_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global SESSION, SubscriptionPoolElement
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import SubscriptionPoolElement


def main():
    print("Resetting all elements")
    SubscriptionPoolElement.query.update({'status': None})
    SESSION.commit()
    base_query = SubscriptionPoolElement.query.filter(SubscriptionPoolElement.status.is_(None))
    print("Updating active elements")
    base_query.filter_by(active=True).update({'status': 'active'})
    print("Updating error elements")
    base_query.filter_by(md5=None).update({'status': 'error'})
    base_query.filter_by(deleted=False, keep='yes').update({'status': 'unlinked'})
    print("Updating duplicate elements")
    base_query.filter_by(deleted=False, keep=None).update({'status': 'duplicate'})
    print("Updating deleted elements")
    base_query.filter_by(deleted=True, keep='no').update({'status': 'deleted'})
    print("Updating archived elements")
    base_query.filter_by(deleted=True, keep=None).update({'status': 'archived'})
    print("Updating unknown elements")
    base_query.update({'status': 'unknown'})
    SESSION.commit()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
