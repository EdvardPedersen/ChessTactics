import re
import subprocess
import time
import io
import threading
from urllib.request import urlopen
import pickle

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

class ChessComDownload(PGNFile):
    def __init__(self, player, year, month):
        url = "https://api.chess.com/pub/player/{}/games/{}/{}/pgn".format(player, year, month)
        self.file = urlopen(url).read().decode("utf-8")
        self.player = player


class ChessGame:
    def __init__(self, game, player):
        self.pgn = io.StringIO(game)
        self.game = chess.pgn.read_game(self.pgn)
        self.player = player
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
            current_score = info["score"].white().score(mate_score=10000)
            if(move.board().turn):
                last_player = "Black"
            else:
                last_player = "White"
            if last_score == None:
                last_score = current_score
            else:
                if abs(last_score - current_score) > 100:
                    if(self.game.headers[last_player] == self.player):
                        self.blunders.append(Tactic(move, current_score))
            last_score = current_score
            
        engine.quit()

    def get_simple(self):
        key = str(self.game.end())
        values = dict()
        values["white"] = self.game.headers["White"]
        values["black"] = self.game.headers["Black"]
        values["player"] = self.player
        blunders = []
        for blunder in self.blunders:
            blunders.append(blunder.get_simple_tactic())
        return key, values, blunders
        

class Tactic:
    def __init__(self, move, score):
        self.move = move
        self.score = score
        self.acceptable_moves = []

    def get_correct_moves(self):
        engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        prev_position = self.move.parent.board()
        moves = []
        for move in prev_position.legal_moves:
            prev_position.push(move)
            info = engine.analyse(prev_position,
                                  chess.engine.Limit(time=0.2),
                                  info=chess.engine.INFO_ALL)
            moves.append((info["score"].white().score(mate_score=10000), move))
            prev_position.pop()
        moves.sort(key=lambda x: x[0])
        played_move = self.score
        if prev_position.turn:
            best_score = moves[-1][0]
            acceptable_moves = [(score, move) for score,move in moves if score > best_score - 30]
        else:
            best_score = moves[0][0]
            acceptable_moves = [(score, move) for score,move in moves if score < best_score + 30]
        engine.quit()
        self.acceptable_moves = acceptable_moves

    def get_simple_tactic(self):
        if len(self.acceptable_moves) < 1:
            raise ValueError("No valid moves found for tactic")
        position = self.move.parent.board().fen()
        bad_move = self.move.uci()
        good_moves = []
        for move in self.acceptable_moves:
            good_moves.append(move[1].uci())
        score = self.score
        return SimpleTactic(position, bad_move, good_moves, score)

class SimpleTactic:
    def __init__(self, position, bad_move, good_moves, score):
        self.position = position
        self.bad_move = bad_move
        self.good_moves = good_moves
        self.score = score

def get_all_tactics(game, queue):
    game.analyze()
    for blunder in game.blunders:
        blunder.get_correct_moves()
    queue.append(game)


        
if __name__ == "__main__":
    with open("p_games", "rb") as f:
        existing_games = pickle.load(f)
    print(existing_games)
    p = ChessComDownload("Rulzern", "2019", "01")
    game_gen = p.get_games()
    game_i = list(game_gen)
    games = []
    threads = []
    for game in game_i[0:1]:
        if game.game.board().fen() in existing_games:
            continue
        t = threading.Thread(target = get_all_tactics, args = (game, games))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    pickled_games = dict()
    for game in games:
        key, values, blunders = game.get_simple()
        pickled_games[key] = (values,blunders)
    with open("p_games", "wb") as f:
        pickle.dump(pickled_games, f)


