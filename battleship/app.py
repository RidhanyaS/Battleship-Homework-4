"""Flask routes for the Battleship web app."""

from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def home():
    """Show the home page."""
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=False)
