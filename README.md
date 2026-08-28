# blindpuzzle

Solve [lichess](https://lichess.org/training) puzzles blindfold, from the terminal.

It prints the position: piece locations, castling rights, the last move, whose
turn it is. Then it runs the puzzle the way the lichess trainer does. You enter
a move. If it's wrong it says so. If it's right it plays the opponent's reply
and waits for your next one.

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

`./puzzle` finds `.venv` on its own. Needs Python 3.8 or later.

On Windows, use `puzzle.cmd` in place of `./puzzle` with the same arguments,
after `py -m venv .venv` and `.venv\Scripts\pip install -r requirements.txt`.
Git Bash and WSL can use `./puzzle`. Colour needs Windows Terminal or
PowerShell 7; set `NO_COLOR=1` if the old console prints stray escape codes.

`./puzzle selftest` checks the install by fetching a few puzzles and solving
them automatically.

## Two sources of puzzles

**The lichess API** needs no download and can filter by theme. It cannot filter
by rating range: lichess offers only a difficulty relative to your own puzzle
rating, and only when authenticated. It also serves one puzzle per request.

**The puzzle database** is lichess's full public export, 6.1 million puzzles
with ratings, themes and openings. It filters on any of them, offline, in well
under a second. One-time setup:

```sh
./puzzle fetch     # 300 MB download
./puzzle index     # builds a 1.4 GB SQLite index, a few minutes
```

Delete the `.csv.zst` archive afterwards if you want the space back. Both files
live in `~/.local/share/blindpuzzle/`, or wherever `$BLINDPUZZLE_DIR` points.
Lichess refreshes the export monthly, so re-run both commands when you want a
newer set.

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
./puzzle play --max-pieces 7             # endgames, by men on the board
./puzzle play --min-pieces 8 --max-pieces 14
./puzzle play --min-plays 1000           # only well-tested puzzles
./puzzle play --opening Sicilian         # or Najdorf, or Kings_Gambit_Accepted
./puzzle play --id sAIXc                 # one specific puzzle
./puzzle play --daily                    # today's lichess puzzle
./puzzle play --seed 42                  # same puzzles again, in the same order
./puzzle play --source api               # ignore the local database

./puzzle themes                          # every theme, with counts
./puzzle themes --top 20
./puzzle stats                           # what's in your local database
```

`-r/--rating` and `--min-rating`/`--max-rating` do the same job; the range form
is shorter. `./puzzle -r 1400-1700` works without typing `play`.

`--min-pieces`/`--max-pieces` count every man on the board, kings and pawns
included. Lichess doesn't publish that, so it's computed from the FEN when the
database is indexed.

[FILTERS.md](FILTERS.md) is the full reference: every flag, all 73 themes with
lichess's own descriptions and counts, and all 156 opening families.
`./puzzle themes` lists them live from your own index. A misspelled theme gets
a suggestion instead of an empty result.

## While solving

Moves go in as SAN (`Nf3`, `exd5`, `Qxg3+`, `O-O`, `e8=Q`) or UCI (`g1f3`,
`e7e8q`). Lowercase piece letters and `0-0` work. Anything illegal or
unreadable is rejected without counting as a wrong answer, so typos cost you
nothing.

| command | |
|---|---|
| `info` / `show` | re-print the position |
| `hint` | names the piece to move, the same hint lichess gives |
| `board` | print the board |
| `solution` | give up and see the line |
| `next` / `skip` | move on |
| `quit` | leave |

A wrong move says so and hands the prompt straight back, so you can type your
next attempt without any keystroke in between. `s` shows the solution, `n`
moves on, `q` leaves. A right move gets the opponent's reply and the prompt
back. Finishing the line prints the solution and offers the next puzzle or the
exit.

If the puzzle ends in mate and you find a different mate, it counts, as on
lichess. A tally prints when you leave.

Rating and themes are spoilers, so they appear only once you're done with a
puzzle. `--show-themes` puts the themes up front.

## How it works

`blindpuzzle/`

| | |
|---|---|
| `model.py` | the `Puzzle` type, and normalising the two sources into it |
| `sources.py` | lichess API client; database download, index and queries |
| `describe.py` | the position readout |
| `session.py` | move parsing and the interactive solving loop |
| `cli.py` | argument handling |

The two sources disagree about where a puzzle starts. The CSV's `FEN` is the
position before the opponent's setup move, and that move is the first entry in
`Moves`. The API's `fen` is the position after it, with the move given
separately as `lastMove`. `/api/puzzle/next` omits both and has to be rebuilt
by replaying the game PGN. All three normalise to one internal shape holding
the position you face and the one before it. That earlier position is what
makes it possible to write the last move in SAN, since SAN is only defined
relative to the position a move was made in.

Move legality, SAN parsing and mate detection come from
[python-chess](https://python-chess.readthedocs.io/). The solution lines are
lichess's.
