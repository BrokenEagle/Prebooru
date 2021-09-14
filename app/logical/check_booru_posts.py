# APP/LOGICAL/CHECK_BOORU_POSTS.PY

# ## LOCAL IMPORTS
from .. import SESSION
from ..models import Post
from ..sources.danbooru_source import GetPostsByMD5s


# ## FUNCTIONS

def CheckAllPostsForDanbooruID():
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
        CheckPostsForDanbooruID(posts)
        max_id = max(post.id for post in posts)
        page += 1


def CheckPostsForDanbooruID(posts):
    post_md5s = [post.md5 for post in posts]
    results = GetPostsByMD5s(post_md5s)
    if results['error']:
        print(results['message'])
        exit(-1)
    if len(results['posts']) > 0:
        dirty = False
        for post in posts:
            danbooru_post = next(filter(lambda x: x['md5'] == post.md5, results['posts']), None)
            if danbooru_post is None:
                continue
            post.danbooru_id = danbooru_post['id']
            dirty = True
            print(".", end="", flush=True)
        if dirty:
            SESSION.commit()
