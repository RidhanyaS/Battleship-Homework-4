"""Flask routes for the Battleship web app."""

from typing import List, Optional

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

if __package__:
    from .game import BOARD_SIZE, SHIP_LENGTHS, Board, Game
else:
    from game import BOARD_SIZE, SHIP_LENGTHS, Board, Game


app = Flask(__name__)
games = {}

FIRE_ERROR_CODES = {
    "The opponent has not joined yet.": "not_joined",
    "The game is already over.": "game_over",
    "It is not this player's turn.": "not_your_turn",
    "A shot has already been fired at that cell.": "already_shot",
    "Row and column must be integers.": "invalid_coordinates",
    "Shot coordinates must be on the board.": "out_of_range",
}
FIRE_ERROR_MESSAGES = {
    "not_joined": "Wait for the other player to join before firing.",
    "game_over": "This game is over. No more shots can be fired.",
    "not_your_turn": "It is not your turn yet.",
    "already_shot": "You have already fired at that cell.",
    "invalid_coordinates": "The row and column must be numbers.",
    "out_of_range": "Choose a cell on the 10 by 10 board.",
    "invalid_shot": "That shot could not be fired.",
}

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

    shot_result = request.args.get("shot_result")
    sunk_ship = request.args.get("sunk_ship")
    if shot_result == "miss":
        shot_message = "Miss."
    elif shot_result == "hit":
        shot_message = "Hit!"
    elif shot_result == "sunk" and sunk_ship in SHIP_LENGTHS:
        shot_message = f"You sunk the {sunk_ship}!"
    else:
        shot_message = None

    fire_error = FIRE_ERROR_MESSAGES.get(request.args.get("fire_error"))

    return render_template(
        "game.html",
        status=game.status,
        turn_message=turn_message,
        can_fire=game.status == "playing" and game.turn == token,
        shot_message=shot_message,
        fire_error=fire_error,
        is_waiting=game.status == "waiting"
        or (game.status == "playing" and game.turn != token),
        game_id=game.game_id,
        creator_token=game.creator_token,
        token=token,
        own_board=board_view(own_board, show_ships=True),
        enemy_board=board_view(opponent_board, show_ships=False),
    )


@app.route("/game/<game_id>/<token>/fire", methods=["POST"])
def fire_shot(game_id, token):
    """Fire at one opponent cell and redirect with the shot result."""
    game = games.get(game_id)
    if game is None or token not in game.players:
        abort(404)

    try:
        row = int(request.form.get("row", ""))
        col = int(request.form.get("col", ""))
    except ValueError:
        return redirect(
            url_for(
                "game_page",
                game_id=game_id,
                token=token,
                fire_error="invalid_coordinates",
            )
        )

    try:
        result, sunk_ship = game.fire(token, row, col)
    except ValueError as error:
        error_code = FIRE_ERROR_CODES.get(str(error))
        if error_code is None:
            raise
        return redirect(
            url_for(
                "game_page",
                game_id=game_id,
                token=token,
                fire_error=error_code,
            )
        )

    result_details = {"shot_result": result}
    if sunk_ship is not None:
        result_details["sunk_ship"] = sunk_ship

    return redirect(
        url_for("game_page", game_id=game_id, token=token, **result_details)
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
