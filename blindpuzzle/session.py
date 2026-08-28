"""The interactive solving loop: lichess puzzle behaviour, without a board."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import chess

from .describe import ascii_board, describe
from .model import Puzzle

SOLVED = "solved"
SOLVED_WITH_HELP = "solved_with_help"
SKIPPED = "skipped"
QUIT = "quit"

_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def c(text: str, code: str) -> str:
    return "\033[{}m{}\033[0m".format(code, text) if _USE_COLOR else text


def green(t): return c(t, "32")
def red(t): return c(t, "31")
def yellow(t): return c(t, "33")
def dim(t): return c(t, "2")
def bold(t): return c(t, "1")


CASTLE_RE = re.compile(r"^[0oO](-[0oO]){1,2}[+#]?$")


def _ambiguity_options(board: chess.Board, text: str) -> List[str]:
    """The legal moves a piece-and-square SAN like 'Rd8' could have meant."""
    match = re.match(r"^([KQRBN])[a-h1-8]*x?([a-h][1-8])", text)
    if not match:
        return []
    piece_type = chess.Piece.from_symbol(match.group(1)).piece_type
    target = chess.parse_square(match.group(2))
    return sorted(
        board.san(m) for m in board.legal_moves
        if m.to_square == target and board.piece_type_at(m.from_square) == piece_type
    )


def parse_move(board: chess.Board, text: str) -> Tuple[Optional[chess.Move], Optional[str]]:
    """Accept SAN or UCI, forgivingly. Returns (move, error_message)."""
    text = text.strip().replace("–", "-").replace("—", "-")
    if not text:
        return None, None

    candidates = [text]
    if CASTLE_RE.match(text):
        candidates.insert(0, text.replace("0", "O").replace("o", "O"))
    # "nf3" -> "Nf3", but leave "b4"/"bxc4" alone first so pawn moves win.
    if len(text) > 2 and text[0] in "nbrqk":
        candidates.append(text[0].upper() + text[1:])
    if len(text) > 2 and text[0] in "NBRQK":
        candidates.append(text[0].lower() + text[1:])

    # UCI first: it is unambiguous.
    if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", text.lower()):
        try:
            move = chess.Move.from_uci(text.lower())
        except ValueError:
            move = None
        if move is not None:
            if move in board.legal_moves:
                return move, None
            return None, "{} isn't legal in this position.".format(text)

    # Valid notation for a move that isn't available is a different mistake from
    # notation that doesn't parse, and saying so saves you re-reading your input.
    best_rank, best_message = -1, None
    for candidate in candidates:
        try:
            return board.parse_san(candidate), None
        except chess.AmbiguousMoveError:
            options = _ambiguity_options(board, candidate)
            message = "{} is ambiguous here{}.".format(
                candidate, ": " + " or ".join(options) if options else "")
            rank = 2
        except chess.IllegalMoveError:
            message = "{} isn't legal in this position.".format(candidate)
            rank = 1
        except ValueError:  # InvalidMoveError, and anything else parse_san raises
            message = "I can't read '{}'. Use SAN (Nf3, exd5, O-O) or UCI (g1f3).".format(text)
            rank = 0
        if rank > best_rank:
            best_rank, best_message = rank, message

    return None, best_message


def format_line(fen: str, ucis: List[str]) -> str:
    """Render a UCI line as numbered SAN, from the given position."""
    board = chess.Board(fen)
    parts = []
    for uci in ucis:
        move = chess.Move.from_uci(uci)
        san = board.san(move)
        if board.turn == chess.WHITE:
            parts.append("{}. {}".format(board.fullmove_number, san))
        elif not parts:
            parts.append("{}... {}".format(board.fullmove_number, san))
        else:
            parts.append(san)
        board.push(move)
    return " ".join(parts)


HELP_TEXT = """
  Enter your move in SAN (Nf3, exd5, Qxg3+, O-O) or UCI (g1f3, e7e8q).
  Other commands:
    info / show    re-print the position
    hint           name the piece to move (counts as help)
    board          print the board
    solution       give up and see the line
    next / skip    move on to the next puzzle
    quit           leave
""".rstrip()


@dataclass
class Stats:
    seen: int = 0
    solved: int = 0
    solved_with_help: int = 0
    skipped: int = 0

    def line(self) -> str:
        return "Puzzles: {} seen, {} solved clean, {} solved with help, {} passed".format(
            self.seen, self.solved, self.solved_with_help, self.skipped)


class Trainer:
    def __init__(self, show_themes: bool = False):
        self.show_themes = show_themes
        self.stats = Stats()

    # -- input ------------------------------------------------------------
    def ask(self, prompt: str) -> str:
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"

    # -- one puzzle -------------------------------------------------------
    def play(self, puzzle: Puzzle) -> str:
        self.stats.seen += 1
        board = puzzle.board()
        opponent = "White" if puzzle.solver_color == chess.BLACK else "Black"
        print()
        print(describe(puzzle, show_themes=self.show_themes))

        index = 0
        used_help = False
        mistakes = 0

        while index < len(puzzle.solution):
            expected = chess.Move.from_uci(puzzle.solution[index])
            answer = self.ask(bold("  > "))
            low = answer.lower()

            if low in ("quit", "q", "exit"):
                return QUIT
            if low in ("next", "skip", "n"):
                self.stats.skipped += 1
                self._reveal(puzzle, board, index, "Passed.")
                return SKIPPED
            if low in ("help", "?"):
                print(dim(HELP_TEXT))
                continue
            if low in ("info", "show", "i", "repeat"):
                print(describe(puzzle, show_themes=self.show_themes))
                continue
            if low in ("board", "b"):
                print(dim(ascii_board(board, puzzle.solver_color)))
                continue
            if low in ("hint", "h"):
                used_help = True
                piece = board.piece_at(expected.from_square)
                print(yellow("  Hint: move your {} on {}.".format(
                    chess.piece_name(piece.piece_type), chess.square_name(expected.from_square))))
                continue
            if low in ("solution", "solve", "answer", "s"):
                self.stats.skipped += 1
                self._reveal(puzzle, board, index, "Solution:")
                return SKIPPED

            move, error = parse_move(board, answer)
            if move is None:
                if error:
                    print(dim("  " + error))
                continue

            san = board.san(move)
            if self._is_correct(board, move, expected):
                board.push(move)
                index += 1
                print(green("  correct: {}".format(san)))
                if board.is_checkmate() or index >= len(puzzle.solution):
                    break
                reply = chess.Move.from_uci(puzzle.solution[index])
                reply_san = board.san(reply)
                board.push(reply)
                index += 1
                print("  {} replies {}".format(opponent, bold(reply_san)))
                continue

            # Legal, but not the puzzle's move.
            mistakes += 1
            print(red("  {} is not the move.".format(san)))
            choice = self.ask(dim("    [k] keep trying   [s] see solution   [n] next puzzle   [q] quit > ")).lower()
            if choice in ("q", "quit", "exit"):
                return QUIT
            if choice in ("n", "next", "skip"):
                self.stats.skipped += 1
                self._reveal(puzzle, board, index, "Passed.")
                return SKIPPED
            if choice in ("s", "solution", "see"):
                self.stats.skipped += 1
                self._reveal(puzzle, board, index, "Solution:")
                return SKIPPED
            continue

        # Solved.
        clean = mistakes == 0 and not used_help
        notes = []
        if mistakes:
            notes.append("{} wrong {}".format(mistakes, "try" if mistakes == 1 else "tries"))
        if used_help:
            notes.append("a hint")
        print()
        print(green(bold("  Solved!")) + "  {}".format(
            "clean" if clean else "with " + " and ".join(notes)))
        print(dim("  Line: {}".format(format_line(puzzle.start_fen, puzzle.solution))))
        print(dim("  " + self._footer(puzzle)))
        if clean:
            self.stats.solved += 1
        else:
            self.stats.solved_with_help += 1
        return SOLVED if clean else SOLVED_WITH_HELP

    def _is_correct(self, board: chess.Board, move: chess.Move, expected: chess.Move) -> bool:
        if move == expected:
            return True
        # lichess accepts any move that mates when the puzzle's move mates.
        probe = board.copy(stack=False)
        probe.push(move)
        if not probe.is_checkmate():
            return False
        probe = board.copy(stack=False)
        probe.push(expected)
        return probe.is_checkmate()

    def _reveal(self, puzzle: Puzzle, board: chess.Board, index: int, label: str) -> None:
        remaining = puzzle.solution[index:]
        print(yellow("  {}".format(label)))
        if remaining and index > 0:
            print("  From here: {}".format(bold(format_line(board.fen(), remaining))))
        print("  Line: {}".format(bold(format_line(puzzle.start_fen, puzzle.solution))))
        print(dim("  " + self._footer(puzzle)))

    def _footer(self, puzzle: Puzzle) -> str:
        """Rating and themes go here, after the fact. Both are spoilers."""
        bits = []
        if puzzle.rating is not None:
            bits.append("rating {}".format(puzzle.rating))
        if puzzle.themes:
            bits.append(", ".join(puzzle.themes))
        bits.append(puzzle.url)
        return "  |  ".join(bits)

    # -- between puzzles --------------------------------------------------
    def continue_prompt(self) -> bool:
        while True:
            answer = self.ask(dim("    [enter] next puzzle   [q] quit > ")).lower()
            if answer in ("", "n", "next", "y", "yes"):
                return True
            if answer in ("q", "quit", "exit"):
                return False
            print(dim("    Press enter for the next puzzle, or q to quit."))
