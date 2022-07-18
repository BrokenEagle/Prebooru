# FIXES/010_SET_MAIN_SIBLING_ON_SIMILARITY_POOL_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global SimilarityPoolElement, SESSION
    sys.path.append(os.path.abspath('.'))
    from app.models import SimilarityPoolElement
    from app import SESSION


def main():
    print("Resetting all elements.")
    SimilarityPoolElement.query.update({'main': False})
    SESSION.commit()
    handled_elements = set()
    q = SimilarityPoolElement.query.order_by(SimilarityPoolElement.id.asc())
    page = q.count_paginate(per_page=1000)
    while True:
        print(f"set_main_sibling_on_similarity_pool_elements: {page.first} - {page.last} / Total({page.count})")
        main_elements = []
        for element in page.items:
            if element.id in handled_elements:
                continue
            main_elements.append(element.id)
            handled_elements.update([element.id, element.sibling_id])
        SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(main_elements)).update({'main': True})
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
