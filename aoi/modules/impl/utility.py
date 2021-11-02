"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from aoi import AoiContextMixin
from aoi.bot import injected


async def baseconvert(
    ctx: AoiContextMixin,
    base1: str,
    base2: str,
    value: str,
    _embed: injected.EmbedCreator,
):
    try:
        dec = int(value, {"hex": 16, "dec": 10, "bin": 2, "oct": 8}[base1])
    except ValueError:
        await ctx.get_builder().as_error().with_description(f"{value} is not a valid {base1} number").send()
        return
    conv = {"hex": hex, "dec": int, "bin": bin, "oct": oct}[base2](dec)
    if base2 == "dec":
        await ctx.get_builder().with_description(f"\n{base1} `{value}` is {base2} `{conv:,}`").send()
    else:
        await ctx.get_builder().with_description(f"\n{base1} `{value}` is {base2} `{conv}`").send()


# TODO add pfact
# TODO add bigmult
# TODO add isprime
