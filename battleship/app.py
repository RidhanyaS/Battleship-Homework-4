"""Flask routes for the Battleship web app."""

from flask import Flask, abort, redirect, render_template, url_for

if __package__:
    from .game import Game
else:
    from game import Game


app = Flask(__name__)
games = {}


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
    """Show the lobby until the game page is implemented."""
    game = games.get(game_id)
    if game is None or token not in game.players:
        abort(404)

    return render_template(
        "waiting.html",
        title="Game lobby",
        message=(
            "Waiting for the other player to join."
            if game.status == "waiting"
            else "Both players have joined. The game board will appear here next."
        ),
        game_status=game.status,
        game_id=game.game_id,
        creator_token=game.creator_token,
        token=token,
    )


if __name__ == "__main__":
    app.run(debug=False)
