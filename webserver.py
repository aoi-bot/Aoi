import os

import redis
from sanic import Sanic
from sanic.response import json
import dotenv

app = Sanic("aoi")
cache = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
dotenv.load_dotenv(".env")
app.config.FORWARDED_SECRET = os.getenv("SANIC")

@app.route("/")
async def main(request):
    return json({
        "members": cache.get("aoi-members"),
        "guilds": cache.get("aoi-guilds")
    }, 200)


app.run(port=8000)
