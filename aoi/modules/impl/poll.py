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


async def poll(ctx: AoiContextMixin, content: str):
    split = content.split(";;")
    if len(split) == 1:
        msg = await ctx.get_builder().with_title(split[0]).with_footer(text=f"Poll by {ctx.author}").send(
            ensure_result=True)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
    else:
        choices = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        msg = (
            await ctx.get_builder()
                .with_title(split[0])
                .with_description("\n".join(f"{choices[n]} {split[n + 1]}" for n in range(len(split) - 1)))
                .with_footer(f"Poll by {ctx.author}")
                .send(ensure_result=True)
        )
        for i in range(len(split) - 1):
            await msg.add_reaction(choices[i])
