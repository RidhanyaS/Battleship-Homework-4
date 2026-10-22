"""Flask routes for the Battleship web app."""

from typing import List, Optional

from flask import Flask, abort, jsonify, redirect, render_template, url_for

if __package__:
    from .game import BOARD_SIZE, Board, Game
else:
    from game import BOARD_SIZE, Board, Game


app = Flask(__name__)
games = {}


def board_view(board: Optional[Board], show_ships: bool) -> List[List[str]]:
    """Build cell states for a page without exposing unshot ship positions."""
    rows = []
    for row in range(BOARD_SIZE):
        cells = []
        for col in range(BOARD_SIZE):
            coordinate = (row, col)
            was_shot = board is not None and coordinate in board.shots
            is_ship = board is not None and (was_shot or show_ships) and any(
                coordinate in ship_cells for ship_cells in board.ships.values()
            )

            if was_shot:
                cells.append("hit" if is_ship else "miss")
            elif show_ships and is_ship:
                cells.append("ship")
            else:
                cells.append("empty")
        rows.append(cells)
    return rows


@app.route("/")
def home():
    """Show the home page."""
    return render_template("home.html")


@app.route("/new", methods=["POST"])
def new_game():
    """Create a game and open its waiting page."""
    game = Game()
    games[game.game_id] = game
    return redirect(
        url_for("game_page", game_id=game.game_id, token=game.creator_token)
    )


@app.route("/join/<game_id>")
def join_game(game_id):
    """Join an existing game and open the new player's page."""
    game = games.get(game_id)
    if game is None:
        abort(404)

    try:
        token = game.join()
    except ValueError:
        return (
            render_template(
                "waiting.html",
                title="Game full",
                message="This game already has two players.",
                game_status=None,
                game_id=None,
                creator_token=None,
                token=None,
            ),
            409,
        )

    return redirect(url_for("game_page", game_id=game_id, token=token))


@app.route("/game/<game_id>/<token>")
def game_page(game_id, token):
    """Show this player's board and only shots fired at the opponent."""
    game = games.get(game_id)
    if game is None or token not in game.players:
        abort(404)

    own_board = game.board_for(token)
    opponent_board = None
    if game.status != "waiting":
        opponent_board = game.opponent_board_for(token)

    if game.status == "waiting":
        turn_message = "Waiting for the other player to join."
    elif game.turn == token:
        turn_message = "It is your turn."
    else:
        turn_message = "Waiting for the opponent's move."

    return render_template(
        "game.html",
        status=game.status,
        turn_message=turn_message,
        is_waiting=game.status == "waiting"
        or (game.status == "playing" and game.turn != token),
        game_id=game.game_id,
        creator_token=game.creator_token,
        token=token,
        own_board=board_view(own_board, show_ships=True),
        enemy_board=board_view(opponent_board, show_ships=False),
    )


@app.route("/game/<game_id>/<token>/status")
def game_status(game_id, token):
    """Return only the state needed for a waiting page to know when to reload."""
    game = games.get(game_id)
    if game is None or token not in game.players:
        abort(404)

    return jsonify(status=game.status, your_turn=game.turn == token)


if __name__ == "__main__":
    app.run(debug=False)
