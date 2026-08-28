from __future__ import annotations

import argparse
import difflib
import sys
from typing import Iterator, List, Optional

from . import sources
from .model import Puzzle
from .session import QUIT, Trainer, dim, yellow

EPILOG = """
examples:
  ./puzzle fetch && ./puzzle index        one-time setup for rating filters (~300 MB)
  ./puzzle play                           random puzzles
  ./puzzle play -r 1400-1700 -t fork      rated 1400-1700, forks only
  ./puzzle play -t mateIn2 -t endgame     both themes at once
  ./puzzle play --id sAIXc                one specific puzzle
  ./puzzle play --daily                   today's lichess puzzle
  ./puzzle themes                         what themes exist, and how many of each
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="puzzle",
        description="Solve lichess puzzles blindfold from the terminal.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    play = sub.add_parser("play", help="solve puzzles (default)")
    play.add_argument("-r", "--rating", metavar="LO-HI",
                      help="rating range, e.g. 1500-1800 (needs the local database)")
    play.add_argument("--min-rating", type=int)
    play.add_argument("--max-rating", type=int)
    play.add_argument("-t", "--theme", action="append", default=[], metavar="THEME",
                      help="puzzle type, repeatable; see './puzzle themes'")
    play.add_argument("--any-theme", action="store_true",
                      help="match any of the given themes instead of all of them")
    play.add_argument("--opening", metavar="TAG", help="filter by opening tag, e.g. Sicilian_Defense")
    play.add_argument("--min-plays", type=int, help="only well-tested puzzles (e.g. 1000)")
    play.add_argument("--min-pieces", type=int, metavar="N",
                      help="fewest men on the board, kings and pawns included")
    play.add_argument("--max-pieces", type=int, metavar="N",
                      help="most men on the board, e.g. --max-pieces 7 for endgames")
    play.add_argument("-n", "--count", type=int, default=10, help="how many puzzles (default 10)")
    play.add_argument("--id", help="one specific puzzle by id")
    play.add_argument("--daily", action="store_true", help="today's lichess puzzle")
    play.add_argument("--source", choices=["auto", "db", "api"], default="auto")
    play.add_argument("--show-themes", action="store_true",
                      help="show themes up front (they are spoilers, so off by default)")
    play.add_argument("--seed", type=int, help="reproducible puzzle order")

    fetch = sub.add_parser("fetch", help="download the lichess puzzle database (~300 MB)")
    fetch.add_argument("--force", action="store_true")

    index = sub.add_parser("index", help="build the searchable index from the download")
    index.add_argument("--limit", type=int, help="index only the first N puzzles (quick test)")
    index.add_argument("--source", help="path to a .csv.zst archive")

    themes = sub.add_parser("themes", help="list puzzle themes with counts")
    themes.add_argument("--top", type=int, help="only the N most common")

    sub.add_parser("stats", help="what's in the local database")

    selftest = sub.add_parser("selftest", help="check the install by auto-solving a few puzzles")
    selftest.add_argument("-n", "--count", type=int, default=3)
    selftest.add_argument("--source", choices=["auto", "db", "api"], default="auto")
    return parser


def parse_rating(args) -> None:
    if not args.rating:
        return
    text = args.rating.replace("..", "-")
    if "-" in text:
        lo, _, hi = text.partition("-")
        if lo.strip():
            args.min_rating = int(lo)
        if hi.strip():
            args.max_rating = int(hi)
    else:  # a bare number means "around here"
        centre = int(text)
        args.min_rating, args.max_rating = centre - 100, centre + 100


def split_themes(values: List[str]) -> List[str]:
    out = []
    for value in values:
        out.extend(part for part in value.replace(",", " ").split() if part)
    return out


def check_themes(themes: List[str]) -> None:
    if not themes or not sources.have_local_db():
        return
    known = {name for name, _ in sources.theme_counts()}
    for theme in themes:
        if theme not in known:
            close = difflib.get_close_matches(theme, known, n=3, cutoff=0.6)
            hint = "  Did you mean: {}?".format(", ".join(close)) if close else \
                   "  Run './puzzle themes' to see the list."
            raise SystemExit("Unknown theme '{}'.\n{}".format(theme, hint))


def puzzle_stream(args) -> Iterator[Puzzle]:
    themes = split_themes(args.theme)

    if args.id or args.daily:
        api = sources.LichessApi()
        yield api.daily() if args.daily else api.by_id(args.id)
        return

    source = args.source
    if source == "auto":
        source = "db" if sources.have_local_db() else "api"
        if source == "api":
            print(dim("No local database yet, using the lichess API."))
            if args.min_rating or args.max_rating or args.min_pieces or args.max_pieces:
                print(yellow("Rating and piece-count filters need the local database: "
                             "run './puzzle fetch && ./puzzle index'. Ignoring them for now."))

    if source == "db":
        check_themes(themes)
        puzzles = sources.query(
            min_rating=args.min_rating, max_rating=args.max_rating,
            themes=themes, match_any=args.any_theme, opening=args.opening,
            min_plays=args.min_plays, min_pieces=args.min_pieces,
            max_pieces=args.max_pieces, count=args.count, seed=args.seed)
        if not puzzles:
            raise SystemExit("No puzzles matched that. Try a wider rating range or fewer themes.")
        if len(puzzles) < args.count:
            print(dim("Only {} puzzles matched.".format(len(puzzles))))
        for puzzle in puzzles:
            yield puzzle
        return

    # API
    if args.min_rating or args.max_rating or args.min_pieces or args.max_pieces:
        print(yellow("The lichess API can't filter by rating or piece count, so those "
                     "are ignored. Use the local database for them."))
    if len(themes) > 1:
        print(yellow("The API takes one theme at a time; using '{}'.".format(themes[0])))
    api = sources.LichessApi()
    for puzzle in api.stream(themes[0] if themes else None, args.count):
        yield puzzle


def run_play(args) -> int:
    parse_rating(args)
    trainer = Trainer(show_themes=args.show_themes)
    stream = puzzle_stream(args)

    first = True
    for puzzle in stream:
        if not first and not trainer.continue_prompt():
            break
        first = False
        outcome = trainer.play(puzzle)
        if outcome == QUIT:
            break
        print()
    else:
        if not first:
            print(dim("\nThat's all the puzzles that matched."))

    print(dim(trainer.stats.line()))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Bare "./puzzle" and "./puzzle -r 1500-1800" both mean play.
    if not argv or (argv[0].startswith("-") and argv[0] not in ("-h", "--help")):
        argv.insert(0, "play")

    args = build_parser().parse_args(argv)
    command = args.command or "play"

    if command == "play":
        return run_play(args)
    if command == "fetch":
        sources.download(force=args.force)
        print("Next:  ./puzzle index")
        return 0
    if command == "index":
        sources.build_index(limit=args.limit, source=args.source)
        return 0
    if command == "themes":
        for theme, n in sources.theme_counts(args.top):
            print("  {:<24} {:>9,}".format(theme, n))
        return 0
    if command == "selftest":
        from . import selftest

        return selftest.run(count=args.count, source=args.source)
    if command == "stats":
        info = sources.db_stats()
        print("  puzzles   {:,}".format(info["count"]))
        print("  ratings   {} - {}".format(info["min_rating"], info["max_rating"]))
        print("  indexed   {}".format(info["built"]))
        print("  location  {}".format(sources.db_path()))
        return 0
    build_parser().print_help()
    return 1
