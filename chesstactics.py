import re
import subprocess
import pexpect
import time

class PGNFile:
    def __init__(self, filename, player):
        self.player = player
        with open(filename) as f:
            self.file = f.read()

    def get_games(self):
        for game in self.file.split("[Event"):
            if game == "":
                continue
            yield ChessGame("[Event" + game, self.player)

class ChessGame:
    def __init__(self, game, player):
        self.player = player
        self.won = False
        self.result = "0.5-0.5"
        for line in game.split('\n'):
            if line.startswith("1."):
                self.moves = line
            elif line.startswith("[White "):
                self.white = re.search('".*"', line).group(0).replace('"', '')
            elif line.startswith("[Black "):
                self.black = re.search('".*"', line).group(0).replace('"', '')
            elif line.startswith("[Result "):
                self.result = re.search('".*"', line).group(0).replace('"', '')
                if self.result == "0-1":
                    if self.black == self.player:
                        self.won = True
                    self.winner = "B"
                elif self.result == "1-0":
                    if self.white == self.player:
                        self.won = True
                    self.winner = "W"

    def __str__(self):
        return "{} vs. {} {}".format(self.white, self.black, self.result)

    def analyze(self):
        print("Starting stockfish")
        stockfish = pexpect.spawn("stockfish")
        print(self.read_uci(stockfish))
        print(stockfish.sendline("uci"))
        print(self.read_uci(stockfish))
        print(stockfish.sendline(b"isready"))
        print(self.read_uci(stockfish))
        print(self.get_moves())

    def read_uci(self, engine):
        time.sleep(0.1)
        output = ""
        try:
            output = output.join(str(engine.read_nonblocking(size = 10000, timeout = 0)))
        except pexpect.TIMEOUT:
            return output
        return output

    def get_moves(self):
        moves = re.findall('\d[\.]* ...', self.moves)
        finalmoves = ""
        for move in moves:
            print(move)
            finalmoves = " ".join([finalmoves, move[-3:].strip()])
        return finalmoves
        

if __name__ == "__main__":
    p = PGNFile("pgn", "Rulzern")
    game_gen = p.get_games()
    game = game_gen.__next__()
    game.analyze()
