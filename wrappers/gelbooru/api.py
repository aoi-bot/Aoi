from dataclasses import dataclass
from typing import List, Tuple, Optional

import aiohttp


@dataclass
class GelbooruPost:
    image_url: str
    tags: List[str]
    page: str
    id: int


# noinspection PyDefaultArgument
class GelbooruBrowser:
    def __init__(self,
                 api_key: str,
                 user_id: str,
                 *,
                 banned_tags: List[str] = []):
        self.banned_tags = banned_tags
        self.api_key = api_key
        self.user_id = user_id

    async def get_posts(self,
                        tags: List[str],
                        *,
                        limit: int = 100,
                        page: int = 0) -> Tuple[Optional[List[GelbooruPost]], bool, bool]:
        filtered_tags = []
        posts = []
        filtered_tag = False
        for i in tags:
            i = i.lower().strip().replace(" ", "_")
            if i not in self.banned_tags:
                filtered_tags.append(i)
            else:
                filtered_tag = True
        if not filtered_tags:
            return None, filtered_tag, False
        async with aiohttp.ClientSession() as sess:
            url = f"https://gelbooru.com/index.php?tags={'+'.join(filtered_tags)}" \
                  f"&api_key={self.api_key}&user_id={self.user_id}" \
                  f"&page=dapi&s=post&q=index&json=1&limit=100"
            async with sess.get(url) as resp:
                js = await resp.json()
                if not js:
                    return None, filtered_tag, False
                for i in js:
                    posts.append(GelbooruPost(
                        image_url=i["file_url"],
                        page=f"https://gelbooru.com/index.php?page=post&s=view&id={i['id']}",
                        id=i["id"],
                        tags=i["tags"].split()
                    ))
        filtered_post = False
        for i in posts:
            if any(e in self.banned_tags for e in i.tags):
                posts.remove(i)
                filtered_post = False
        return posts, filtered_tag, filtered_post
