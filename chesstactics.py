import re
import subprocess
import time
import io

import pexpect
import chess.pgn
import chess.engine

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
        self.pgn = io.StringIO(game)
        self.game = chess.pgn.read_game(self.pgn)
        self.player = player
        self.won = player in self.game.headers["Termination"]
        self.blunders = []

    def __str__(self):
        return "{} vs. {} {}".format(self.game.headers["White"], self.game.headers["Black"], self.game.headers["Result"])

    def analyze(self):
        engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        board = chess.Board()
        last_score = None
        for move in self.game.mainline():
            info = engine.analyse(move.board(),
                                  chess.engine.Limit(time=0.1),
                                  info=chess.engine.INFO_ALL)
            current_score = info["score"].white().score(mate_score=1000)
            if(move.board().turn):
                last_player = "Black"
            else:
                last_player = "White"
            if last_score == None:
                last_score = current_score
            else:
                if abs(last_score - current_score) > 100:
                    if(self.game.headers[last_player] == self.player):
                        self.blunders.append(move)
            last_score = current_score
            
        engine.quit()

if __name__ == "__main__":
    p = PGNFile("pgn", "Rulzern")
    game_gen = p.get_games()
    game = game_gen.__next__()
    game.analyze()
    print(game.blunders)
