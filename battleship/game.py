"""Core Battleship game logic. This module does not depend on Flask."""

import random
import secrets
from typing import Dict, Optional, Set, Tuple


BOARD_SIZE = 10
SHIP_LENGTHS = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}
Coordinate = Tuple[int, int]
ShotResult = Tuple[str, Optional[str]]


class Board:
    """A player's board, including ships and shots received from the opponent."""

    def __init__(self) -> None:
        self.ships: Dict[str, Set[Coordinate]] = {}
        self.shots: Set[Coordinate] = set()
        self._place_ships()

    def _place_ships(self) -> None:
        """Place each ship randomly without allowing ships to overlap."""
        occupied: Set[Coordinate] = set()

        for ship_name, length in SHIP_LENGTHS.items():
            while True:
                row = random.randrange(BOARD_SIZE)
                col = random.randrange(BOARD_SIZE)
                horizontal = random.choice([True, False])

                if horizontal:
                    cells = {(row, col + offset) for offset in range(length)}
                else:
                    cells = {(row + offset, col) for offset in range(length)}

                if all(
                    0 <= ship_row < BOARD_SIZE and 0 <= ship_col < BOARD_SIZE
                    for ship_row, ship_col in cells
                ) and not cells.intersection(occupied):
                    self.ships[ship_name] = cells
                    occupied.update(cells)
                    break

    def receive_shot(self, row: int, col: int) -> ShotResult:
        """Record a shot and return (miss, None), (hit, None), or (sunk, name)."""
        if not isinstance(row, int) or not isinstance(col, int):
            raise ValueError("Row and column must be integers.")
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise ValueError("Shot coordinates must be on the board.")
        if (row, col) in self.shots:
            raise ValueError("A shot has already been fired at that cell.")

        coordinate = (row, col)
        self.shots.add(coordinate)

        for ship_name, cells in self.ships.items():
            if coordinate in cells:
                if cells.issubset(self.shots):
                    return "sunk", ship_name
                return "hit", None

        return "miss", None

    def all_sunk(self) -> bool:
        """Return True when every ship cell has been hit."""
        return all(cells.issubset(self.shots) for cells in self.ships.values())


class Game:
    """A two-player game. Player tokens also identify whose turn it is."""

    def __init__(self) -> None:
        self.game_id = secrets.token_urlsafe(8)
        self.creator_token = secrets.token_urlsafe(8)
        self.players: Dict[str, Board] = {self.creator_token: Board()}
        self.status = "waiting"
        self.turn: Optional[str] = None
        self.winner: Optional[str] = None

    def join(self) -> str:
        """Add the second player and return their secret token."""
        if self.status != "waiting":
            raise ValueError("This game is already full.")

        player_token = secrets.token_urlsafe(8)
        self.players[player_token] = Board()
        self.status = "playing"
        self.turn = self.creator_token
        return player_token

    def board_for(self, player_token: str) -> Board:
        """Return a player's own board, or raise ValueError for an invalid token."""
        if player_token not in self.players:
            raise ValueError("Invalid player token.")
        return self.players[player_token]

    def opponent_board_for(self, player_token: str) -> Board:
        """Return the other player's board without exposing it to the player."""
        self.board_for(player_token)
        for token, board in self.players.items():
            if token != player_token:
                return board
        raise ValueError("The opponent has not joined yet.")

    def fire(self, player_token: str, row: int, col: int) -> ShotResult:
        """Fire a shot for the current player and advance or finish the game."""
        self.board_for(player_token)

        if self.status == "waiting":
            raise ValueError("The opponent has not joined yet.")
        if self.status == "finished":
            raise ValueError("The game is already over.")
        if player_token != self.turn:
            raise ValueError("It is not this player's turn.")

        opponent_board = self.opponent_board_for(player_token)
        result = opponent_board.receive_shot(row, col)
        if opponent_board.all_sunk():
            self.status = "finished"
            self.winner = player_token
        else:
            for token in self.players:
                if token != player_token:
                    self.turn = token
                    break

        return result
