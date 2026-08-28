# blindpuzzle

Solve [lichess](https://lichess.org/training) puzzles blindfold, from the terminal.

It prints the position — piece locations, castling rights, the last move (in
SAN, with where the piece came from), whose turn it is — and then plays the
puzzle the way the lichess trainer does: you
enter a move, it tells you if it's wrong, and if it's right it answers with the
opponent's reply and waits for your next one.

```
--------------------------------------------------------------
  Puzzle 09CvB
--------------------------------------------------------------
  White
    King     h2
    Queen    h3
    Rook     d7
    Bishops  b3, h4
    Pawns    a4, b2, c3, f2, g5
  Black
    King     g8
    Queen    e2
    Rooks    d8, f8
    Bishop   b6
    Pawns    a5, b7, c7, e5, f7, g7

  Castling   none
  Last move  30... Rad8  (rook a8 to d8)
  White to move
--------------------------------------------------------------
  > Bxf7+
  correct: Bxf7+
  Black replies Rxf7
  > Rxd8+
  correct: Rxd8+

  Solved!  clean
  Line: 31. Bxf7+ Rxf7 32. Rxd8+
  rating 1798  |  crushing, deflection, kingsideAttack  |  lichess.org/training/09CvB
```

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

That's it — `./puzzle` finds `.venv` on its own. Requires Python 3.8+.

Check it works (solves a few puzzles automatically):

```sh
./puzzle selftest
```

## Two sources of puzzles

**The lichess API** works immediately, no download. It can filter by theme but
**not by rating range** — lichess only offers a difficulty relative to your own
puzzle rating, and only when authenticated. It also serves one puzzle per
request, so a run of ten is ten polite HTTP calls.

**The puzzle database** is lichess's full public export: ~5.9 million puzzles
with ratings, themes and openings. Filters on anything, instantly, offline.
One-time setup:

```sh
./puzzle fetch     # ~300 MB download
./puzzle index     # builds ~1.1 GB of searchable SQLite; takes a few minutes
```

After indexing you can delete the `.csv.zst` archive. Both live in
`~/.local/share/blindpuzzle/` (override with `$BLINDPUZZLE_DIR`). Re-run both
commands whenever you want a fresher set — lichess updates the export monthly.

`./puzzle play` uses the database if it's there and the API if it isn't.

## Usage

```sh
./puzzle play                            # random puzzles
./puzzle play -r 1400-1700               # rating range (database only)
./puzzle play -r 1600                    # shorthand for 1500-1700
./puzzle play -t fork                    # one theme
./puzzle play -t mateIn2 -t endgame      # both themes
./puzzle play -t pin -t skewer --any-theme
./puzzle play -r 1800-2100 -t sacrifice -n 20
./puzzle play --min-plays 1000           # only well-tested puzzles
./puzzle play --opening Sicilian          # or Najdorf, or Kings_Gambit_Accepted
./puzzle play --id sAIXc                 # one specific puzzle
./puzzle play --daily                    # today's lichess puzzle
./puzzle play --seed 42                  # same puzzles again, in the same order
./puzzle play --source api               # ignore the local database

./puzzle themes                          # every theme, with counts
./puzzle themes --top 20
./puzzle stats                           # what's in your local database
```

Both `-r/--rating` and the separate `--min-rating`/`--max-rating` work; the
range form is just shorter. `./puzzle -r 1400-1700` (no `play`) works too.

**[FILTERS.md](FILTERS.md) is the full reference** — every flag, all 73 themes
with lichess's own descriptions and counts, and all 156 opening families. For a
live listing from your own index, `./puzzle themes`. A misspelled theme gets a
suggestion rather than an empty result.

## While solving

Enter moves in **SAN** (`Nf3`, `exd5`, `Qxg3+`, `O-O`, `e8=Q`) or **UCI**
(`g1f3`, `e7e8q`). Lowercase piece letters and `0-0` are accepted. Anything
illegal or unreadable is rejected without counting as a wrong answer, so a typo
costs you nothing.

| command | |
|---|---|
| `info` / `show` | re-print the position |
| `hint` | names the piece you should move (same hint lichess gives) |
| `board` | prints the board — defeats the purpose, but it's there |
| `solution` | give up, see the whole line |
| `next` / `skip` | move on |
| `quit` | leave |

**Wrong move** → it says so and offers: keep trying, see the solution, next
puzzle, or quit. **Right move** → it plays the opponent's reply and asks for
your next move, until the line is done. **Solved** → success message with the
full line and the puzzle's themes, then next puzzle or quit.

As on lichess, if the puzzle ends in mate and you find a *different* mate, that
counts. A running tally prints when you exit.

The puzzle's rating and themes are spoilers, so they appear only once you're
done with it. `--show-themes` puts the themes up front if you want them.

## How it works

`blindpuzzle/`

| | |
|---|---|
| `model.py` | the `Puzzle` type, and normalising the two sources into it |
| `sources.py` | lichess API client; database download, index and queries |
| `describe.py` | the blindfold readout |
| `session.py` | move parsing and the interactive solving loop |
| `cli.py` | argument handling |

One wrinkle worth knowing, since it bites everyone who touches this data: the
two sources disagree about where a puzzle starts. The CSV's `FEN` is the
position *before* the opponent's setup move, with that move first in `Moves`.
The API's `fen` is the position *after* it, with the move given separately as
`lastMove`. Both are normalised to the same internal shape, which keeps both
the position you face and the one before it — you need the earlier one to write
the last move in SAN at all, since SAN is only defined relative to the position
the move was made in.

Move legality, SAN parsing and check/mate detection are
[python-chess](https://python-chess.readthedocs.io/); the solution lines are
lichess's own.
