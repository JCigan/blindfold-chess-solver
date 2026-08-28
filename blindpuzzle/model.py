"""Puzzle model plus normalisation of the two lichess sources.

The two sources describe the same thing with different conventions:

* The CSV database gives a FEN for the position *before* the opponent's move
  that sets the puzzle up, and ``Moves[0]`` is that setup move.  The solver
  moves second.
* The API gives ``fen`` for the position *after* that move (i.e. the one the
  solver actually faces), with the setup move separately in ``lastMove``, and
  ``solution[0]`` is already the solver's move.

Internally we keep both: ``prev_fen`` (before the setup move, needed to render
the last move in SAN and to say what it captured) and ``start_fen`` (what the
solver faces).  ``solution`` is always the solver's line, starting with the
solver's own first move and alternating from there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import chess


def _fen_key(fen: str) -> str:
    """Placement + side to move + castling; ignores ep/clock representation."""
    parts = fen.split()
    return " ".join(parts[:3])


@dataclass
class Puzzle:
    id: str
    start_fen: str
    solution: List[str]
    prev_fen: Optional[str] = None
    setup_move: Optional[str] = None
    rating: Optional[int] = None
    themes: List[str] = field(default_factory=list)
    plays: Optional[int] = None
    popularity: Optional[int] = None
    game_url: Optional[str] = None

    @property
    def url(self) -> str:
        return "https://lichess.org/training/{}".format(self.id)

    @property
    def solver_color(self) -> bool:
        return chess.Board(self.start_fen).turn

    @property
    def solver_color_name(self) -> str:
        return "White" if self.solver_color == chess.WHITE else "Black"

    def board(self) -> chess.Board:
        return chess.Board(self.start_fen)

    @property
    def solver_move_count(self) -> int:
        """How many moves the solver has to find."""
        return (len(self.solution) + 1) // 2

    @classmethod
    def from_csv_row(cls, row: dict) -> "Puzzle":
        moves = row["Moves"].split()
        prev_fen = row["FEN"]
        board = chess.Board(prev_fen)
        board.push(chess.Move.from_uci(moves[0]))
        return cls(
            id=row["PuzzleId"],
            start_fen=board.fen(),
            solution=moves[1:],
            prev_fen=prev_fen,
            setup_move=moves[0],
            rating=_int(row.get("Rating")),
            themes=(row.get("Themes") or "").split(),
            plays=_int(row.get("NbPlays")),
            popularity=_int(row.get("Popularity")),
            game_url=row.get("GameUrl") or None,
        )

    @classmethod
    def from_db_row(cls, row) -> "Puzzle":
        return cls.from_csv_row(
            {
                "PuzzleId": row["id"],
                "FEN": row["fen"],
                "Moves": row["moves"],
                "Rating": row["rating"],
                "Themes": row["themes"],
                "NbPlays": row["plays"],
                "Popularity": row["popularity"],
                "GameUrl": None,
            }
        )

    @classmethod
    def from_api(cls, payload: dict) -> "Puzzle":
        p = payload["puzzle"]
        game = payload.get("game") or {}
        pgn = game.get("pgn")
        start_fen = p.get("fen")
        last_move = p.get("lastMove")
        prev_fen = None

        if start_fen and last_move and pgn:
            prev_fen = _prev_fen_from_pgn(pgn, start_fen, last_move)
        elif pgn and p.get("initialPly") is not None:
            # /api/puzzle/next omits fen and lastMove. Only /daily and
            # /api/puzzle/{id} include them, so replay the game instead.
            prev_fen, start_fen, last_move = _positions_from_pgn(
                pgn, p["initialPly"], p["solution"][0])
        if not start_fen:
            raise ValueError(
                "puzzle {} came back without a position or a replayable game".format(p.get("id")))
        game_url = None
        if game.get("id"):
            game_url = "https://lichess.org/{}#{}".format(
                game["id"], p.get("initialPly", "")
            )
        return cls(
            id=p["id"],
            start_fen=start_fen,
            solution=list(p["solution"]),
            prev_fen=prev_fen,
            setup_move=last_move,
            rating=p.get("rating"),
            themes=list(p.get("themes") or []),
            plays=p.get("plays"),
            game_url=game_url,
        )


def _prev_fen_from_pgn(pgn: str, start_fen: str, last_move: str) -> Optional[str]:
    """Replay the game to recover the position before the puzzle's setup move.

    The API hands us the position the solver faces but not the one before it,
    and you cannot un-make a move without knowing what it captured, so this
    replays the game's SAN and stops at the ply that reproduces ``start_fen``.
    """
    board = chess.Board()
    target = _fen_key(start_fen)
    for san in pgn.split():
        try:
            move = board.parse_san(san)
        except ValueError:
            return None
        before = board.fen()
        uci = move.uci()
        board.push(move)
        if uci == last_move and _fen_key(board.fen()) == target:
            return before
    return None


def _positions_from_pgn(pgn: str, initial_ply: int, first_solution_move: str):
    """Rebuild (prev_fen, start_fen, last_move) by replaying the game's SAN.

    The puzzle begins after ``initialPly + 1`` plies; the ply at that boundary
    is the opponent's setup move.  Verified against payloads that carry both
    ``fen`` and ``initialPly``, and re-checked here by requiring the puzzle's
    own first move to be legal in the position we land on.
    """
    board = chess.Board()
    moves = pgn.split()
    for offset in (1, 0):
        board.reset()
        stop = initial_ply + offset
        if stop > len(moves) or stop < 1:
            continue
        try:
            for san in moves[:stop]:
                board.push_san(san)
        except ValueError:
            continue
        last = board.pop()          # stop >= 1, so there is always one to take back
        prev_fen = board.fen()
        board.push(last)
        try:
            candidate = chess.Move.from_uci(first_solution_move)
        except ValueError:
            candidate = None
        if candidate is not None and candidate in board.legal_moves:
            return prev_fen, board.fen(), last.uci()
    raise ValueError("could not reconstruct the puzzle position from the game")


def _int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
