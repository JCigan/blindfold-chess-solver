"""Check an install end to end: fetch a few puzzles and solve them automatically.

Drives the real Trainer with scripted input, so a pass means the readout
renders, moves parse, replies come back, and puzzles complete.
"""

from __future__ import annotations

import contextlib
import io
from typing import List

import chess

from . import sources
from .describe import describe
from .model import Puzzle
from .session import SOLVED, Trainer, parse_move


class ScriptedTrainer(Trainer):
    def __init__(self, answers: List[str]):
        super().__init__()
        self.answers = list(answers)

    def ask(self, prompt: str) -> str:
        return self.answers.pop(0) if self.answers else "quit"


def solver_moves_san(puzzle: Puzzle) -> List[str]:
    board = puzzle.board()
    answers = []
    for i, uci in enumerate(puzzle.solution):
        move = chess.Move.from_uci(uci)
        if i % 2 == 0:
            answers.append(board.san(move))
        board.push(move)
    return answers


def check(puzzle: Puzzle) -> List[str]:
    problems = []

    text = describe(puzzle)
    if puzzle.id not in text or "to move" not in text or "Last move" not in text:
        problems.append("readout looks wrong")
    if puzzle.rating is not None and str(puzzle.rating) in text:
        problems.append("rating leaked into the readout")

    board = puzzle.board()
    for uci in puzzle.solution:
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            problems.append("illegal move in solution: {}".format(uci))
            break
        board.push(move)

    first = chess.Move.from_uci(puzzle.solution[0])
    san = puzzle.board().san(first)
    for form in (san, first.uci(), san.lower()):
        parsed, error = parse_move(puzzle.board(), form)
        if parsed != first:
            problems.append("failed to parse '{}' ({})".format(form, error or "wrong move"))

    with contextlib.redirect_stdout(io.StringIO()) as captured:
        outcome = ScriptedTrainer(solver_moves_san(puzzle)).play(puzzle)
    if outcome != SOLVED:
        problems.append("correct answers did not solve it (got {}); output was:\n{}".format(
            outcome, captured.getvalue()))

    return problems


def run(count: int = 3, source: str = "auto") -> int:
    if source == "auto":
        source = "db" if sources.have_local_db() else "api"

    print("Self-test using the {}...".format(
        "local database" if source == "db" else "lichess API"))
    if source == "db":
        # A narrow band keeps the seeded ordering cheap on the full database.
        puzzles = sources.query(min_rating=1500, max_rating=1600, count=count, seed=20240101)
    else:
        puzzles = list(sources.LichessApi().stream(count=count))

    if not puzzles:
        print("FAIL: no puzzles came back")
        return 1

    failures = 0
    for puzzle in puzzles:
        problems = check(puzzle)
        if problems:
            failures += 1
            print("  FAIL {}: {}".format(puzzle.id, "; ".join(problems)))
        else:
            print("  ok   {} (rating {}, {} moves)".format(
                puzzle.id, puzzle.rating, puzzle.solver_move_count))

    print("{}/{} puzzles passed.".format(len(puzzles) - failures, len(puzzles)))
    return 1 if failures else 0
