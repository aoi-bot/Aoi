import os
import re
from io import BytesIO

import dotenv
import random
import redis
from PIL import Image, ImageDraw, ImageFont
from sanic import Sanic, response
from sanic.response import json

app = Sanic("aoi")
cache = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
dotenv.load_dotenv(".env")
app.config.FORWARDED_SECRET = os.getenv("SANIC")

with open("assets/ttt-template.png", "rb") as fp:
    image: Image.Image = Image.open(fp)
    image.load()
    font = ImageFont.truetype("assets/merged.ttf", size=80)
aoi_purple = 0x63, 0x44, 0x87


@app.route("/")
async def main(request):
    return json({
        "members": cache.get("aoi-members"),
        "guilds": cache.get("aoi-guilds"),
        "success": True
    }, 200, headers={"Access-Control-Allow-Origin": "*"})


@app.route("/tictactoe")
async def ttt(request):
    query = request.args
    if "board" not in query:
        return json({
            "success": False,
            "error": "board parameter missing"
        }, 400)
    board: str = query.pop("board")[0]
    if not re.match(r"[xo-]{9}", board):
        return json({
            "success": False,
            "error": "board parameter malformed"
        }, 400)
    copy: Image.Image = image.copy()
    drw = ImageDraw.Draw(copy)
    pairs = [
        [56, 83],
        [210, 83],
        [355, 83],
        [56, 220],
        [210, 220],
        [355, 220],
        [56, 336],
        [210, 336],
        [355, 336]
    ]
    for i, char in enumerate(board):
        x = pairs[i][0] + random.randrange(-10, 10)
        y = pairs[i][1] + random.randrange(-10, 10)
        if char != "-":
            drw.text((x, y), char.upper(), font=font, fill=aoi_purple)

    io = BytesIO()
    copy.save(io, format="PNG")
    io.seek(0)

    return response.stream(lambda resp: resp.write(io.read()), content_type="image/png")



app.run(port=8000)
