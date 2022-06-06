# APP/LOGICAL/CHECK/POSTS.PY

# ## LOCAL IMPORTS
from ...models import Post
from ..database.post_db import update_post_from_parameters
from ..sources.danbooru import get_posts_by_md5s


# ## FUNCTIONS

def check_all_posts_for_danbooru_id():
    print("Checking all posts for Danbooru ID.")
    query = Post.query.filter(Post.danbooru_id == None)  # noqa: E711
    max_id = 0
    page = 1
    page_count = (query.get_count() // 100) + 1
    while True:
        posts = query.filter(Post.id > max_id).limit(100).all()
        if len(posts) == 0:
            return
        print("\n%d/%d" % (page, page_count))
        if not check_posts_for_danbooru_id(posts):
            return
        max_id = max(post.id for post in posts)
        page += 1


def check_posts_for_danbooru_id(posts):
    post_md5s = [post.md5 for post in posts]
    for i in range(0, len(post_md5s), 100):
        md5_sublist = post_md5s[i: i + 100]
        results = get_posts_by_md5s(md5_sublist)
        if results['error']:
            print(results['message'])
            return False
        if len(results['posts']) > 0:
            for post in posts:
                danbooru_post = next(filter(lambda x: x['md5'] == post.md5, results['posts']), None)
                if danbooru_post is None:
                    continue
                update_post_from_parameters(post, {'danbooru_id': danbooru_post['id']})
    return True
