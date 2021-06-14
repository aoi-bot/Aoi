import io
from datetime import datetime
from functools import reduce
from io import BytesIO
from typing import Optional, Dict, Any, Tuple

import aiohttp
import sympy
from PIL import Image
from PIL import ImageOps

import aoi
from discord.ext import commands, tasks
from libs.converters import integer, allowed_strings, dtime
from libs.expressions import evaluate, get_prime_factors
from wrappers import gmaps as gmaps
from wrappers import weather as wx


class Utility(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.cur_rates = {}
        # self._currency_update.start()
        self.wx: Optional[wx.WeatherGov] = None
        bot.loop.create_task(self._init())
        self.sat_cache: Dict[str, Tuple[datetime, Any]] = {}
        self.apod_cache: Dict[str, Tuple[str, str, str, str]] = {}
        self.gmap: Optional[gmaps.GeoLocation] = None
        self.wx = wx.WeatherGov(self.bot.weather_gov)

    async def _init(self):
        self.bot.logger.info("util:Waiting for bot")
        await self.bot.wait_until_ready()
        self.gmap = self.bot.gmap
        self.bot.logger.info("util:Ready!")

    @property
    def description(self) -> str:
        return "Various utility commands"

    # region # NASA

    @commands.command(
        brief="Get a LANDSAT-8 image of a lat/long",
        description="""
        landsat 15.6 176.7
        landsat Chicago
        """
    )
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def landsat(self, ctx: aoi.AoiContext, coords: gmaps.LocationCoordinates,
                      date: dtime() = None):
        lat = coords.lat
        long = coords.long
        dt = date or datetime.now()
        url = f"https://api.nasa.gov/planetary/earth/imagery?" \
              f"lon={long}&lat={lat}&dim=0.15&api_key={self.bot.nasa}" \
              f"&date={dt.strftime('%Y-%m-%d')}"
        buf = io.BytesIO()
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    buf.write(await resp.content.read())
        await ctx.embed(
            title=f"{lat} {long} {dt.strftime('%Y-%m-%d')}",
            image=buf
        )

    # @commands.cooldown(1, 360, type=commands.BucketType.user)
    @commands.command(
        brief="Gets the astronomy picture of the day",
        description="""
        apod 12/25/2005
        """
    )
    async def apod(self, ctx: aoi.AoiContext, *, date: dtime() = None):
        if not date:
            date = datetime.datetime.now()
        dt = date.strftime('%Y-%m-%d')
        if dt not in self.apod_cache:
            async with ctx.typing():
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(f"https://api.nasa.gov/planetary/apod?api_key={self.bot.nasa}&"
                                        f"date={dt}") as resp:
                        js = await resp.json()
            if js.get("code", None) in [404, 400, 403, 401]:
                self.apod_cache[dt] = (str(js["code"]), "404", "404",
                                       js["msg"])
                return await ctx.send_error(js["msg"])
            url = js["url"]
            hdurl = js.get("hdurl", url)
            expl = js["explanation"][:1900]
            title = js["title"] + " " + dt
            self.apod_cache[dt] = (title, hdurl, url, expl)
        else:
            title, hdurl, url, expl = self.apod_cache[dt]
            if title == "404":
                await ctx.send_error(expl)
        await ctx.embed(
            title=title,
            description=f"{expl}\n\n[Normal Resolution]({url})  [High Resolution]({hdurl})",
            image=url
        )

    # endregion

    # region # wx

    @commands.command(
        brief="Look up a looping radar"
    )
    async def radarloop(self, ctx: aoi.AoiContext, location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat, location.long)
        await ctx.embed(
            image=f"https://radar.weather.gov/ridge/lite/{res.radar_station}_loop.gif"
        )

    # @commands.command(
    #     brief="Look up a current satellite image",
    #     aliases=["radar"]
    # )
    async def satellite(self, ctx: aoi.AoiContext,
                        location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat,
                                        location.long)
        radar = res.radar_station[-3:]
        if radar in self.sat_cache:
            diff = (datetime.now() - self.sat_cache[radar][0]).seconds
            if diff < 30 * 60:
                img = self.sat_cache[radar][1]
                buf = io.BytesIO()
                img.save(buf, format="png")
                return await ctx.embed(image=buf, footer=f"Cached from {diff // 60}m{diff % 60:2} ago")
            del self.sat_cache[radar]
        urls = [
            f"https://radar.weather.gov/ridge/Overlays/Topo/Short/{radar}_Topo_Short.jpg",
            f"https://radar.weather.gov/ridge/RadarImg/N0R/{radar}_N0R_0.gif",
            f"https://radar.weather.gov/ridge/Overlays/County/Short/{radar}_County_Short.gif",
            f"https://radar.weather.gov/ridge/Overlays/Rivers/Short/{radar}_Rivers_Short.gif",
            f"https://radar.weather.gov/ridge/Overlays/Highways/Short/{radar}_Highways_Short.gif",
            f"https://radar.weather.gov/ridge/Overlays/Cities/Short/{radar}_City_Short.gif",
            f"https://radar.weather.gov/ridge/Warnings/Short/{radar}_Warnings_0.gif",
            f"https://radar.weather.gov/ridge/Legend/N0R/{radar}_N0R_Legend_0.gif"
        ]
        imgs = []
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                for url in urls:
                    async with sess.get(url) as resp:
                        buf = io.BytesIO()
                        buf.write(await resp.content.read())
                        buf.seek(0)
                        imgs.append(Image.open(buf, "png").convert("RGBA"))
        composite = reduce(lambda i1, i2: Image.alpha_composite(i1, i2), imgs)
        self.sat_cache[radar] = (datetime.now(), composite)
        buf = io.BytesIO()
        composite.save(fp=buf, format="png")
        await ctx.embed(
            image=buf
        )

    @commands.command(
        brief="View the raw data for a lat/long",
        description="""
        wxraw Chicago
        wxraw 124 123.6
        """
    )
    async def wxraw(self, ctx: aoi.AoiContext, *,
                    location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat,
                                        location.long)
        await ctx.embed(
            title=f"{res.point}",
            fields=[
                ("Grid", f"{res.grid_x},{res.grid_y}"),
                ("Radar", res.radar_station),
                ("Timezone", res.time_zone),
                ("Endpoints", f"[Hourly]({res.forecast_hourly_endpoint})\n"
                              f"[Grid]({res.forecast_grid_data_endpoint})\n"
                              f"[Extended]({res.forecast_endpoint})\n")
            ]
        )

    @commands.cooldown(1, 60, type=commands.BucketType.user)
    @commands.command(
        brief="Look up an hourly forecast",
        description="""
        wxhourly Chicago
        """
    )
    async def wxhourly(self, ctx: aoi.AoiContext, *, location: gmaps.LocationCoordinates):
        async with ctx.typing():
            conditions = (await self.wx.lookup_hourly(location))
        await ctx.paginate(
            fmt=f"Resolved Address: {location.location or location}```%s```\n",
            lst=[cond.line() for cond in conditions],
            n=24,
            title="Weather lookup",
            thumbnails=[c.icon for c in conditions[3::24]]
        )

    # endregion

    # region # Utility

    @commands.command(
        brief="Get basic geolocation data on an address",
        description="""
        geolookup 111 W Aoi Way, Hanakoville, TBHK
        """
    )
    async def geolookup(self, ctx: aoi.AoiContext, *, address):
        result = (await self.gmap.lookup_address(address))[0]
        await ctx.embed(
            title="Geolocation Lookup",
            fields=[
                       ("Looked up address", address),
                       ("Resolved address", result.formatted_address),
                       ("Location", result.geometry.location)
                   ] + ([
                            ("Bounds", f"{result.geometry.northeast}\n"
                                       f"{result.geometry.southwest}\n")
                        ] if result.geometry.northeast else []),
            not_inline=[0, 1, 2]
        )

    @commands.command(
        brief="Find the prime factorization of a number",
        aliases=["pfact", "factor"]
    )
    async def primefactor(self, ctx: aoi.AoiContext, number: integer(max_digits=8)):
        pfact = get_prime_factors(number)
        await ctx.send_info(
            f"Prime factorization of {number} is ```\n"
            f"{'*'.join((str(n) + '^' + str(c) if c > 1 else str(n)) for n, c in pfact.items())}\n"
            f"```",
            user=None
        )

    @commands.command(
        brief="Checks to see if a number is prime"
    )
    async def isprime(self, ctx: aoi.AoiContext, number: integer(max_digits=8,
                                                                 force_positive=True)):
        await ctx.send_info(
            f"{number} is {'not' if len(get_prime_factors(number).keys()) > 1 else ''} prime"
        )

    # @commands.command(
    #     brief="Evaluates an expression"
    # )
    async def calc(self, ctx: aoi.AoiContext, *, expr: str):
        try:
            res = await evaluate(expr)
        except aoi.CalculationSyntaxError:
            await ctx.send_error("Syntax error")
        except aoi.DomainError as e:
            await ctx.send_error(f"Domain error for {e}")
        except aoi.MathError:
            await ctx.send_error("Math error")
        else:
            await ctx.send_info(f"Expression Result:\n{res}")

    @commands.command(
        brief="Converts between bases",
        aliases=["baseconv", "bconv"]
    )
    async def baseconvert(self, ctx: aoi.AoiContext,
                          base1: allowed_strings("hex", "dec", "bin", "oct"),
                          base2: allowed_strings("hex", "dec", "bin", "oct"),
                          value: str):
        try:
            dec = int(value, {"hex": 16,
                              "dec": 10,
                              "bin": 2,
                              "oct": 8}[base1])
        except ValueError:
            raise commands.BadArgument(f"\n{value} is not a valid {base1} number")
        conv = {"hex": hex,
                "dec": int,
                "bin": bin,
                "oct": oct}[base2](dec)
        if base2 == "dec":
            return await ctx.send_info(f"\n{base1} `{value}` is {base2} `{conv:,}`")
        return await ctx.send_info(f"\n{base1} `{value}` is {base2} `{conv}`")

    @commands.command(
        brief="Multiply two large numbers",
        aliases=["bmult"]
    )
    async def bigmultiply(self, ctx: aoi.AoiContext,
                          num1: int,
                          num2: int):
        await ctx.send_info(f"\n`{num1:,}` * `{num2:,}` = `{num1 * num2:,}`")

    @commands.command(
        brief="Render LaTeX",
    )
    async def latex(self, ctx: aoi.AoiContext, *, formula: str):
        await ctx.trigger_typing()
        buffer = BytesIO()
        try:
            sympy.preview(f"$${formula.strip('`')}$$", viewer="BytesIO", outputbuffer=buffer,
                          dvioptions=["-T", "tight", "-z", "0", "--truecolor", "-D 150"])
        except RuntimeError:
            await ctx.send_error("An error occurred while rendering.")
        result = BytesIO()
        buffer.seek(0)
        old = Image.open(buffer)
        ImageOps.expand(old, border=20, fill=(0xff, 0xff, 0xff)).save(result, format="png")
        await ctx.embed(image=result)

    # endregion


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Utility(bot))
