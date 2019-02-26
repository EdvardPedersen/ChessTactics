import threading
import pickle
import random

from flask import Flask, render_template, send_from_directory

import chesstactics

app = Flask("Chess tactics")

with open("games.dat", "rb") as f:
    games = pickle.load(f)

num_tactics = 0
for value in games.items():
    num_tactics += len(value[1][1])
print("Total tactics {}".format(num_tactics))
print("In {} games".format(len(games)))
analysis_threads = []
new_games = []

def update_games():
    for t in analysis_threads:
        if not t.is_alive():
            analysis_threads.remove(t)
    if len(new_games) == 0:
        return
    for game in new_games:
        key, values, blunders = game.get_simple()
        games[key] = (values, blunders)
    with open("games.dat", "wb") as f:
        pickle.dump(games, f)

@app.route("/img/<path:path>")
def serve_images(path):
    return send_from_directory("static/img/", path)

@app.route("/")
def get_tactics():
    update_games()
    print(games)
    game = random.choice(list(games))
    values = games[game]
    headers = values[0]
    blunders = values[1]
    current_blunder = random.choice(blunders)

    fen_string = game
    bad_move_start = current_blunder.bad_move[:2]
    bad_move_stop = current_blunder.bad_move[2:]
    acceptable_moves = " ".join(current_blunder.good_moves)

    return render_template('show_tactic.html', fen_string=current_blunder.position, bad_start = bad_move_start, bad_stop = bad_move_stop, good_moves = acceptable_moves)

@app.route("/get_tactic/<player>/<year>/<month>")
def init_tactics(player, year, month):
    update_games()
    pgn = chesstactics.ChessComDownload(player, year, month)
    for game in pgn.get_games():
        if str(game.game.end()) in games:
            print("FEN in DB {}".format(str(game.game.end())))
            continue
        thread = threading.Thread(target = chesstactics.get_all_tactics, args = (game, new_games))
        analysis_threads.append(thread)
        thread.start()
    return "{} threads analyzing your problems".format(len(analysis_threads))

@app.route("/success")
def good_work():
    update_games()
    return "Real good work"
