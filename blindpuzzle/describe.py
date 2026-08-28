"""The position readout: piece locations, castling rights, last move, turn."""

from __future__ import annotations

from typing import List, Optional

import chess

from .model import Puzzle

PIECE_ORDER = [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
PIECE_LABEL = {
    chess.KING: ("King", "Kings"),
    chess.QUEEN: ("Queen", "Queens"),
    chess.ROOK: ("Rook", "Rooks"),
    chess.BISHOP: ("Bishop", "Bishops"),
    chess.KNIGHT: ("Knight", "Knights"),
    chess.PAWN: ("Pawn", "Pawns"),
}


def _squares(board: chess.Board, color: bool, piece_type: int) -> List[int]:
    squares = list(board.pieces(piece_type, color))
    # File-major reads more naturally than a1..h8 when you are visualising.
    return sorted(squares, key=lambda s: (chess.square_file(s), chess.square_rank(s)))


def side_lines(board: chess.Board, color: bool) -> List[str]:
    lines = []
    for piece_type in PIECE_ORDER:
        squares = _squares(board, color, piece_type)
        if not squares:
            continue
        singular, plural = PIECE_LABEL[piece_type]
        label = singular if len(squares) == 1 else plural
        lines.append("    {:<8} {}".format(
            label, ", ".join(chess.square_name(s) for s in squares)))
    return lines


def castling_text(board: chess.Board) -> str:
    parts = []
    for color, name in ((chess.WHITE, "White"), (chess.BLACK, "Black")):
        rights = []
        if board.has_kingside_castling_rights(color):
            rights.append("O-O")
        if board.has_queenside_castling_rights(color):
            rights.append("O-O-O")
        if rights:
            parts.append("{} {}".format(name, " and ".join(rights)))
    return "; ".join(parts) if parts else "none"


def last_move_text(puzzle: Puzzle) -> str:
    if not puzzle.setup_move:
        return "unknown (position given without its preceding move)"
    move = chess.Move.from_uci(puzzle.setup_move)
    if not puzzle.prev_fen:
        return "{}-{}".format(
            chess.square_name(move.from_square), chess.square_name(move.to_square))

    before = chess.Board(puzzle.prev_fen)
    san = before.san(move)

    # Number from the position you face: the API renumbers puzzle FENs from
    # move 1, so numbering off the real game would contradict the solution line.
    start = chess.Board(puzzle.start_fen)
    if start.turn == chess.BLACK:
        prefix = "{}.".format(start.fullmove_number)
    else:
        prefix = "{}...".format(max(1, start.fullmove_number - 1))

    return "{} {}  ({})".format(prefix, san, _origin(before, move))


def _origin(before: chess.Board, move: chess.Move) -> str:
    """Where the piece came from. SAN alone often doesn't say."""
    if before.is_castling(move):
        return "castles {}".format(
            "kingside" if chess.square_file(move.to_square) > 4 else "queenside")

    piece = before.piece_at(move.from_square)
    detail = "{} {}".format(
        chess.piece_name(piece.piece_type), chess.square_name(move.from_square))

    if before.is_en_passant(move):
        detail += " takes the pawn on {} en passant".format(chess.square_name(move.to_square))
    else:
        captured = before.piece_at(move.to_square)
        if captured is not None:
            detail += " takes the {} on {}".format(
                chess.piece_name(captured.piece_type), chess.square_name(move.to_square))
        else:
            detail += " to {}".format(chess.square_name(move.to_square))
    if move.promotion:
        detail += ", promoting to {}".format(chess.piece_name(move.promotion))
    return detail


def describe(puzzle: Puzzle, show_themes: bool = False, width: int = 62) -> str:
    board = puzzle.board()
    rule = "-" * width

    header = "  Puzzle {}".format(puzzle.id)
    if show_themes and puzzle.themes:
        header += "  |  {}".format(", ".join(puzzle.themes))

    out = [rule, header, rule]
    for color, name in ((chess.WHITE, "White"), (chess.BLACK, "Black")):
        out.append("  {}".format(name))
        out.extend(side_lines(board, color))
    out.append("")
    out.append("  Castling   {}".format(castling_text(board)))
    out.append("  Last move  {}".format(last_move_text(puzzle)))
    out.append("  {} to move".format(puzzle.solver_color_name))
    out.append(rule)
    return "\n".join(out)


def ascii_board(board: chess.Board, perspective: Optional[bool] = None) -> str:
    """Print the board, for when you are stuck."""
    flipped = perspective == chess.BLACK
    text = str(board.transform(chess.flip_vertical).transform(chess.flip_horizontal)) if flipped else str(board)
    rows = text.split("\n")
    ranks = range(1, 9) if flipped else range(8, 0, -1)
    files = "hgfedcba" if flipped else "abcdefgh"
    lines = ["  {}  {}".format(r, row) for r, row in zip(ranks, rows)]
    lines.append("     " + " ".join(files))
    return "\n".join(lines)
