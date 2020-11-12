import aoi


class Game:
    def __init__(self, ctx: aoi.AoiContext):
        self.ctx = ctx

    async def play(self):
        raise NotImplementedError()
