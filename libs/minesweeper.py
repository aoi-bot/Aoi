import random


class SpoilerMinesweeper:
    WON = 1
    CONTINUE = 0
    LOST = 2

    BOMB = -1
    UNCOVERED = -2

    def __init__(self, height: int = 10, width: int = 10, bombs: int = 10):
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        if bombs > height * width:
            raise MinesweeperError("Number of bombs cannot be bigger than the number of squares")
        placed = 0
        while placed < bombs:
            h = random.randint(0, height - 1)
            w = random.randint(0, width - 1)
            if self.board[h][w] == 0:
                self.board[h][w] = -1
                placed += 1
        for h in range(height):
            for w in range(width):
                if self.board[h][w] == -1:
                    continue
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if h + dx < 0 or w + dy < 0 or h + dx >= height or w + dy >= width:
                            continue
                        if not dx and not dy:
                            continue
                        if self.board[h + dx][w + dy] == -1:
                            self.board[h][w] += 1

        print(self)

    def __str__(self):
        return "\n".join(["".join(map(self._str, row)) for row in self.board])

    def discord_str(self, spoilers: bool = True):
        d_str = "\n".join(["".join(map(lambda x: self._discord_str(x, spoilers), row)) for row in self.board])
        if len(d_str) >= 1900:
            raise MinesweeperError("Board to big to send through discord")
        return d_str

    def _str(self, n: int):
        if n == -1:
            return "*"
        if n == 0:
            return "-"
        return str(n)

    def _discord_str(self, n: int, spoiler: bool = False):
        fmt = "||:%s:||" if spoiler else ":%s:"
        if n == -1:
            return fmt % "bomb"
        else:
            return fmt % ['black_large_square', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'][n]


class MinesweeperError(Exception):
    pass
