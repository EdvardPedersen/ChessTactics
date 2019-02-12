from flask import Flask, render_template, send_from_directory

import chesstactics

app = Flask("Chess tactics")

@app.route("/img/<path:path>")
def serve_images(path):
    return send_from_directory("static/img/", path)

@app.route("/")
def get_tactics():
    pgn = chesstactics.PGNFile("pgn", "Rulzern")
    game_gen = pgn.get_games()
    current_game = game_gen.__next__()
    current_game.analyze()
    current_game.blunders[0].get_correct_moves()
    move = current_game.blunders[0].move
    bad_move_start = move.move.uci()[:2]
    bad_move_stop = move.move.uci()[2:]
    board = move.parent.board()
    extracted_fen = board.fen()
    print(extracted_fen)
    return render_template('show_tactic.html', fen_string=extracted_fen, bad_start = bad_move_start, bad_stop = bad_move_stop)
