import random
import urllib.parse
from typing import Tuple

import aiohttp


class Imgur:
    def __init__(self, user: str):
        self.user = user

    async def random_by_tag(self, tag: str) -> Tuple[str, str, str, str]:
        url = f"https://api.imgur.com/3/gallery/t/{urllib.parse.quote_plus(tag)}"
        headers = {"Authorization": f"Client-ID {self.user}"}

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, headers=headers) as resp:
                js = random.choice((await resp.json())["data"]["items"])

        return (
            (js["images"][0]["id"] if js["is_album"] else js["id"]),
            js["id"],
            js["link"],
            js["images"][0]["description"],
        )
