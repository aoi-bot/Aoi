import random

from .base import Game


class RPS(Game):
    def __init__(self, ctx, turns):
        self.turns = turns
        super(RPS, self).__init__(ctx)

    async def play(self):
        def point(a: str, b: str):
            a, b = a[0], b[0]
            return {
                "rr": 0,
                "pp": 0,
                "ss": 0,
                "rp": 1,
                "pr": -1,
                "sp": -1,
                "ps": 1,
                "sr": 1,
                "rs": -1
            }[a + b]

        conv = {
            "r": "Rock",
            "p": "Paper",
            "s": "Scissors"
        }
        win = ["You got a point!", "It's a tie!", "I got a point!"]
        final = ["You win!", "It's a tie!", "I win."]
        user = 0
        comp = 0
        phrase = ""
        for i in range(self.turns):
            await self.ctx.send(f"{phrase}\n**Round {i + 1}**\nInput R P or S\n\n"
                                f"**Current Score**\n{self.score(comp, user)}\n")
            choice = (await self.ctx.input(str, "cancel", lambda x: x[0].lower() in ["r", "p", "s"]))[0]
            if not choice:
                break
            compch = random.choice(["r", "p", "s"])
            dev = point(choice, compch)
            if dev == 1:
                comp += 1
            if dev == -1:
                user += 1
            phrase = f"**{win[dev + 1]}** I got **{conv[compch]}**, and you got **{conv[choice]}**\n"
        await self.ctx.send(
            f"{phrase}\n**Game over**\n{final[1 if comp == user else 2 if comp > user else 0]}\n\n"
            f"**Final Score**\n{self.score(comp, user)}")
