import threading
import pickle
import random
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, render_template, send_from_directory, request

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
thread_pool = ThreadPoolExecutor(max_workers = 8)
new_games = []

def update_games():
    for t in analysis_threads:
        if t.done():
            analysis_threads.remove(t)
    if len(new_games) == 0:
        return
    for game in new_games:
        key, values, blunders = game.get_simple()
        games[key] = (values, blunders)
    print("Total games: {}".format(len(games)))
    with open("games.dat", "wb") as f:
        pickle.dump(games, f)

@app.route("/img/<path:path>")
def serve_images(path):
    return send_from_directory("static/img/", path)

@app.route("/tactics/img/<path:path>")
def serve_images_tactics(path):
    return send_from_directory("static/img/", path)

@app.route("/tactics/<player>")
def get_tactics(player):
    update_games()
    our_games = {x:games[x] for x in games if games[x][0]["player"] == player}

    got_blunder = False
    while not got_blunder:
        game = random.choice(list(our_games))
        values = our_games[game]
        headers = values[0]
        blunders = values[1]
        if len(blunders) > 0:
            got_blunder = True
    current_blunder = random.choice(blunders)

    fen_string = game
    bad_move_start = current_blunder.bad_move[:2]
    bad_move_stop = current_blunder.bad_move[2:]
    acceptable_moves = " ".join(current_blunder.good_moves)

    return render_template('show_tactic.html',
                           fen_string=current_blunder.position,
                           bad_start = bad_move_start,
                           bad_stop = bad_move_stop,
                           good_moves = acceptable_moves,
                           player_name = headers["player"],
                           white = headers["white"],
                           black = headers["black"])

@app.route("/")
def frontpage():
    return render_template('add_tactic.html')

@app.route("/view_tactics")
def route_to_tactics():
    name = request.args.get('username','')
    return get_tactics(name)

@app.route("/get_tactics")
def route_to_init_tactics():
    name = request.args.get('username','')
    year = request.args.get('year','2019')
    month = request.args.get('month','01')
    return init_tactics(name, year, month)

@app.route("/get_tactic/<player>/<year>/<month>")
def init_tactics(player, year, month):
    update_games()
    pgn = chesstactics.ChessComDownload(player, year, month)
    for game in pgn.get_games():
        if str(game.game.end()) in games:
            print("FEN in DB {}".format(str(game.game.end())))
            continue
        thread = thread_pool.submit(chesstactics.get_all_tactics, game, new_games)
        analysis_threads.append(thread)
    return "{} threads analyzing your problems".format(len(analysis_threads))

@app.route("/success")
def good_work():
    update_games()
    return "Real good work"
