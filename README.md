# Battleship

A two-player Battleship web game built with Flask for a class assignment. Each
player opens the game in their own browser and takes turns firing at the other
player's board.

## What I built

- Randomly placed fleets on 10 by 10 boards: Carrier (5), Battleship (4),
  Cruiser (3), Submarine (3), and Destroyer (2).
- A two-player lobby with a shareable join link and automatic status checks
  while waiting.
- Turn-based firing with hit, miss, and sunk results, plus win/loss messages.
- An opponent board that shows only the results of shots already fired. Unshot
  ship positions are not sent to the opponent's page.
- A responsive pink-themed game page and a How to play page.
- Game state stored in an in-memory Python dictionary; no database, accounts,
  cookies, or WebSockets are used.

## Project structure

```text
battleship/
  app.py
  game.py
  templates/
    base.html
    error.html
    game.html
    home.html
    how_to_play.html
    waiting.html
  static/
    style.css
requirements.txt
```

## Setup and run

Run these commands from the repository root.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install Flask:

```bash
pip install -r requirements.txt
```

Start the server from the `battleship` directory:

```bash
cd battleship
flask --app app run --port 5001
```

Open <http://127.0.0.1:5001/> in a browser. Select **New game**, then share the
join link with the second player. To test locally, open the join link in a
second browser window (or an incognito window).
On macOS, port 5000 is often used by AirPlay Receiver and shows a 403 error, so this app runs on port 5001.


The game runs on the local development server. Since game data is held in
memory, restarting the server ends all current games. The player tokens are
part of each player's game URL; keep those URLs private.
