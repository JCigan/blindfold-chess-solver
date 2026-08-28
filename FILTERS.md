# Filtering puzzles

Everything you can select on, and every value it takes. Counts come from the
6,100,960 puzzles indexed on 2026-08-27 17:48; `./puzzle themes` prints them live from your own
index, which is the authority if lichess has added anything since.

## Quick reference

| flag | what it does |
|---|---|
| `-r LO-HI`, `--rating` | rating range, e.g. `-r 1400-1700` |
| `--min-rating N`, `--max-rating N` | the same, one end at a time |
| `-t THEME`, `--theme` | puzzle type; repeatable, all must match |
| `--any-theme` | make repeated `-t` mean *any* rather than *all* |
| `--opening TAG` | opening family or variation, matched as a substring |
| `--min-plays N` | only puzzles played at least N times |
| `-n N`, `--count` | how many puzzles this session (default 10) |
| `--id ID` | one specific puzzle |
| `--daily` | today's lichess puzzle |
| `--seed N` | reproducible selection: same filters and seed, same puzzles |
| `--source db\|api\|auto` | force a source (default: database if indexed) |
| `--show-themes` | reveal themes before you solve instead of after |

Rating and `--opening` need the local database; themes work against either
source, though the API takes only one at a time.

## Rating

```sh
./puzzle play -r 2200-2500      # a range
./puzzle play -r 2400           # shorthand for 2300-2500
./puzzle play -r 2600-          # open-ended
./puzzle play --min-rating 2000 # same thing, spelled out
```

Ratings in the database run 399 to 3322. They are lichess puzzle ratings, which
drift well above player ratings at the top end -- a 2500 puzzle is not a
position a 2500 player finds automatically, since the rating reflects how
often solvers actually fail it.

## Themes

```sh
./puzzle play -t smotheredMate
./puzzle play -t fork -t endgame       # both
./puzzle play -t pin -t skewer --any-theme
./puzzle play -t "fork,pin"            # commas work too
```

Most puzzles carry several themes at once -- a short mating tactic is usually
tagged `mate`, `mateIn2`, `short` and `middlegame` together -- so stacking them
narrows the field quickly. A misspelling gets a suggestion rather than an empty
result.

### How the puzzle ends

What you are playing for.

| theme | puzzles | |
|---|--:|---|
| `mate` | 1,937,001 | Win the game with style. |
| `crushing` | 2,337,681 | Spot the opponent blunder to obtain a crushing advantage. (eval ≥ 600cp) |
| `advantage` | 1,759,458 | Seize your chance to get a decisive advantage. (200cp ≤ eval ≤ 600cp) |
| `equality` | 12,875 | Come back from a losing position, and secure a draw or a balanced position. (eval ≤ 200cp) |

### Length

How many moves you have to find.

| theme | puzzles | |
|---|--:|---|
| `oneMove` | 900,761 | A puzzle that is only one move long. |
| `short` | 3,066,077 | Two moves to win. |
| `long` | 1,582,976 | Three moves to win. |
| `veryLong` | 497,201 | Four moves or more to win. |

### Game phase

| theme | puzzles | |
|---|--:|---|
| `opening` | 290,640 | A tactic during the first phase of the game. |
| `middlegame` | 2,748,814 | A tactic during the second phase of the game. |
| `endgame` | 3,061,506 | A tactic during the last phase of the game. |

### Endgame type

These all carry `endgame` as well.

| theme | puzzles | |
|---|--:|---|
| `pawnEndgame` | 226,113 | An endgame with only pawns. |
| `rookEndgame` | 328,813 | An endgame with only rooks and pawns. |
| `bishopEndgame` | 83,602 | An endgame with only bishops and pawns. |
| `knightEndgame` | 50,677 | An endgame with only knights and pawns. |
| `queenEndgame` | 71,272 | An endgame with only queens and pawns. |
| `queenRookEndgame` | 46,069 | An endgame with only queens, rooks and pawns. |

### Mate in N

| theme | puzzles | |
|---|--:|---|
| `mateIn1` | 898,212 | Deliver checkmate in one move. |
| `mateIn2` | 807,425 | Deliver checkmate in two moves. |
| `mateIn3` | 196,470 | Deliver checkmate in three moves. |
| `mateIn4` | 28,698 | Deliver checkmate in four moves. |
| `mateIn5` | 6,198 | Figure out a long mating sequence. |

### Named mating patterns

| theme | puzzles | |
|---|--:|---|
| `backRankMate` | 206,205 | Checkmate the king on the home rank, when it is trapped there by its own pieces. |
| `smotheredMate` | 24,039 | A checkmate delivered by a knight in which the mated king is unable to move because it is surrounded (or smothered) by its own pieces. |
| `anastasiaMate` | 7,441 | A knight and rook or queen team up to trap the opposing king between the side of the board and a friendly piece. |
| `arabianMate` | 7,474 | A knight and a rook team up to trap the opposing king on a corner of the board. |
| `balestraMate` | 1,364 | A bishop delivers the checkmate, while a queen blocks the remaining escape squares |
| `blindSwineMate` | 6,361 | Two rooks team up to mate the king in an area of 2 by 2 squares. |
| `bodenMate` | 3,720 | Two attacking bishops on criss-crossing diagonals deliver mate to a king obstructed by friendly pieces. |
| `cornerMate` | 10,783 | Confine the king to the corner using a rook or queen and a knight to engage the checkmate. |
| `doubleBishopMate` | 3,710 | Two attacking bishops on adjacent diagonals deliver mate to a king obstructed by friendly pieces. |
| `dovetailMate` | 4,013 | A queen delivers mate to an adjacent king, whose only two escape squares are obstructed by friendly pieces. |
| `epauletteMate` | 22,648 | Two adjacent escape squares for a checked king are occupied by other pieces. |
| `hookMate` | 10,625 | Checkmate with a rook, knight, and pawn along with one enemy pawn to limit the enemy king's escape. |
| `killBoxMate` | 5,440 | A rook is next to the enemy king and supported by a queen that also blocks the king's escape squares. The rook and the queen catch the enemy king in a 3 by 3 "kill box". |
| `morphysMate` | 7,133 | Use the bishop to check the king, while your rook helps to confine it. |
| `operaMate` | 63,940 | Check the king with a rook and use a bishop to defend the rook. |
| `pillsburysMate` | 67,645 | The rook delivers checkmate, while the bishop helps to confine it. |
| `swallowstailMate` | 8,397 | A checkmate pattern that visually resembles the appearance of a swallow’s tail, similar to a V shape. |
| `triangleMate` | 7,741 | The queen and rook, one square away from the enemy king, are on the same rank or file, separated by one square, forming a triangle. |
| `vukovicMate` | 2,445 | A rook and knight team up to mate the king. The rook delivers mate while supported by a third piece, and the knight is used to block the king's escape squares. |

### Tactical motifs

| theme | puzzles | |
|---|--:|---|
| `fork` | 781,815 | A move where the moved piece attacks two opponent pieces at once. |
| `pin` | 366,063 | A tactic involving pins, where a piece is unable to move without revealing an attack on a higher value piece. |
| `skewer` | 134,756 | A motif involving a high value piece being attacked, moving out the way, and allowing a lower value piece behind it to be captured or attacked, the inverse of a pin. |
| `discoveredAttack` | 308,426 | Moving a piece (such as a knight), that previously blocked an attack by a long range piece (such as a rook), out of the way of that piece. |
| `doubleCheck` | 31,924 | Checking with two pieces at once, as a result of a discovered attack where both the moving piece and the unveiled piece attack the opponent's king. |
| `discoveredCheck` | 108,797 | Move a piece to reveal a check from a hidden attacking piece, which often leads to a decisive advantage. |
| `deflection` | 264,141 | A move that distracts an opposing piece from another duty that it performs, such as guarding a key square. Sometimes also called "overloading". |
| `attraction` | 221,076 | An exchange or sacrifice encouraging or forcing an opponent piece to a square that allows a follow-up tactic. |
| `clearance` | 80,366 | A move, often with tempo, that clears a square, file or diagonal for a follow-up tactical idea. |
| `interference` | 21,971 | Moving a piece between two opponent pieces to leave one or both opponent pieces undefended, such as a knight on a defended square between two rooks. |
| `intermezzo` | 73,026 | Instead of playing the expected move, first interpose another move posing an immediate threat that the opponent must answer. Also known as "Zwischenzug" or "In between". |
| `xRayAttack` | 21,731 | A piece attacks or defends a square, through an enemy piece. |
| `capturingDefender` | 39,872 | Removing a piece that is critical to defence of another piece, allowing the now undefended piece to be captured on a following move. |
| `hangingPiece` | 222,062 | A tactic involving an opponent piece being undefended or insufficiently defended and free to capture. |
| `trappedPiece` | 66,999 | A piece is unable to escape capture as it has limited moves. |
| `sacrifice` | 459,732 | A tactic involving giving up material in the short-term, to gain an advantage again after a forced sequence of moves. |
| `zugzwang` | 63,821 | The opponent is limited in the moves they can make, and all moves worsen their position. |
| `quietMove` | 255,381 | A move that does not check, capture, or create an immediate threat to capture. Instead, it prepares a hidden and unavoidable threat for a later move. |
| `defensiveMove` | 368,191 | A precise move or sequence of moves that is needed to avoid losing material or another advantage. |
| `collinearMove` | 7,736 | Two opposing pieces face each other, and one slides along the line of attack without capturing the enemy piece. |

### Attack and king safety

| theme | puzzles | |
|---|--:|---|
| `kingsideAttack` | 533,171 | An attack of the opponent's king, after they castled on the king side. |
| `queensideAttack` | 92,460 | An attack of the opponent's king, after they castled on the queen side. |
| `exposedKing` | 183,318 | A tactic involving a king with few defenders around it, often leading to checkmate. |
| `attackingF2F7` | 44,812 | An attack focusing on the f2 or f7 pawn, such as in the fried liver opening. |

### Pawns and special moves

| theme | puzzles | |
|---|--:|---|
| `advancedPawn` | 379,076 | One of your pawns is deep into the opponent position, maybe threatening to promote. |
| `promotion` | 146,745 | Promote one of your pawn to a queen or minor piece. |
| `underPromotion` | 1,123 | Promotion to a knight, bishop, or rook. |
| `enPassant` | 8,580 | A tactic involving the en passant rule, where a pawn can capture an opponent pawn that has bypassed it using its initial two-square move. |
| `castling` | 2,486 | Bring the king to safety, and deploy the rook for attack. |

### Where the game came from

| theme | puzzles | |
|---|--:|---|
| `master` | 834,842 | Puzzles from games played by titled players. |
| `masterVsMaster` | 76,730 | Puzzles from games between two titled players. |
| `superGM` | 3,228 | Puzzles from games played by the best players in the world. |

## Openings

```sh
./puzzle play --opening Sicilian                    # the whole family
./puzzle play --opening Sicilian_Defense_Najdorf    # one variation
./puzzle play --opening Kings_Gambit -r 2000-2400   # with anything else
```

1,214,759 puzzles carry an opening tag: 156 families and 1,589 distinct
variation tags. Tags are lichess's opening names with underscores for spaces,
and a puzzle usually carries both its family and its variation
(`Sicilian_Defense Sicilian_Defense_Najdorf_Variation`). Matching is on
substrings, so `--opening Sicilian` catches every Sicilian and `--opening
Najdorf` catches the Najdorf under any spelling of its parent.

Note that an opening *tag* is not the `opening` *theme*: 1,214,759 puzzles are
tagged with an opening, while 290,640 carry the `opening` theme, which means the
puzzle occurs during the opening phase. A tagged puzzle can be a middlegame.

### Every family

| opening | puzzles |
|---|--:|
| `Sicilian_Defense` | 189,118 |
| `French_Defense` | 80,957 |
| `Queens_Pawn_Game` | 73,986 |
| `Caro-Kann_Defense` | 69,848 |
| `Italian_Game` | 69,202 |
| `Scandinavian_Defense` | 54,250 |
| `Queens_Gambit_Declined` | 45,965 |
| `English_Opening` | 38,591 |
| `Ruy_Lopez` | 36,887 |
| `Scotch_Game` | 34,595 |
| `Indian_Defense` | 33,731 |
| `Philidor_Defense` | 22,898 |
| `Kings_Gambit_Accepted` | 18,900 |
| `Zukertort_Opening` | 18,643 |
| `Four_Knights_Game` | 18,328 |
| `Russian_Game` | 18,278 |
| `Modern_Defense` | 17,954 |
| `Pirc_Defense` | 17,648 |
| `Vienna_Game` | 17,533 |
| `Bishops_Opening` | 16,862 |
| `Slav_Defense` | 16,324 |
| `Kings_Pawn_Game` | 15,489 |
| `Queens_Gambit_Accepted` | 12,543 |
| `Benoni_Defense` | 12,000 |
| `Nimzowitsch_Defense` | 11,613 |
| `Nimzo-Larsen_Attack` | 11,610 |
| `Alekhine_Defense` | 10,893 |
| `Kings_Indian_Defense` | 10,839 |
| `Englund_Gambit` | 9,942 |
| `Horwitz_Defense` | 9,780 |
| `Kings_Gambit_Declined` | 9,669 |
| `Owen_Defense` | 9,555 |
| `Bird_Opening` | 9,301 |
| `Dutch_Defense` | 8,518 |
| `Petrovs_Defense` | 8,167 |
| `Nimzo-Indian_Defense` | 7,306 |
| `Vant_Kruijs_Opening` | 6,770 |
| `Semi-Slav_Defense` | 6,624 |
| `Center_Game` | 6,427 |
| `Hungarian_Opening` | 5,570 |
| `Elephant_Gambit` | 5,309 |
| `Ponziani_Opening` | 5,152 |
| `Three_Knights_Opening` | 4,914 |
| `Blackmar-Diemer_Gambit` | 4,557 |
| `Rapport-Jobava_System` | 4,377 |
| `Polish_Opening` | 4,339 |
| `Englund_Gambit_Complex` | 4,295 |
| `Rat_Defense` | 4,127 |
| `English_Defense` | 4,007 |
| `Trompowsky_Attack` | 4,004 |
| `Grunfeld_Defense` | 3,852 |
| `Kings_Indian_Attack` | 3,844 |
| `Kings_Gambit` | 3,653 |
| `Danish_Gambit_Accepted` | 3,336 |
| `Grob_Opening` | 3,314 |
| `Danish_Gambit` | 3,148 |
| `Van_Geet_Opening` | 2,675 |
| `Englund_Gambit_Declined` | 2,308 |
| `Blackmar-Diemer_Gambit_Accepted` | 2,266 |
| `Old_Indian_Defense` | 2,263 |
| `Kings_Knight_Opening` | 2,242 |
| `Tarrasch_Defense` | 2,211 |
| `Reti_Opening` | 2,198 |
| `Catalan_Opening` | 2,104 |
| `Mieses_Opening` | 1,901 |
| `Queens_Indian_Defense` | 1,637 |
| `London_System` | 1,489 |
| `Latvian_Gambit` | 1,447 |
| `St_George_Defense` | 1,344 |
| `Czech_Defense` | 1,341 |
| `Torre_Attack` | 1,338 |
| `Mikenas_Defense` | 1,290 |
| `Duras_Gambit` | 1,268 |
| `Saragossa_Opening` | 1,257 |
| `East_Indian_Defense` | 1,061 |
| `Richter-Veresov_Attack` | 1,036 |
| `Vienna_Gambit_with_Max_Lange_Defense` | 999 |
| `Latvian_Gambit_Accepted` | 985 |
| `Benko_Gambit` | 863 |
| `Blackmar-Diemer_Gambit_Declined` | 780 |
| `Englund_Gambit_Complex_Declined` | 778 |
| `Yusupov-Rubinstein_System` | 729 |
| `Bogo-Indian_Defense` | 681 |
| `Danish_Gambit_Declined` | 672 |
| `Borg_Defense` | 670 |
| `Neo-Grunfeld_Defense` | 659 |
| `Benko_Gambit_Accepted` | 643 |
| `Pterodactyl_Defense` | 623 |
| `Anderssens_Opening` | 609 |
| `Kadas_Opening` | 583 |
| `Giuoco_Piano` | 525 |
| `Rapport-Jobava_System_with_e6` | 495 |
| `Polish_Defense` | 486 |
| `Lion_Defense` | 482 |
| `Kings_Pawn_Opening` | 457 |
| `Slav_Indian` | 453 |
| `Barnes_Opening` | 434 |
| `Queens_Gambit` | 422 |
| `Mexican_Defense` | 397 |
| `Queens_Indian_Accelerated` | 387 |
| `Ware_Opening` | 366 |
| `Canard_Opening` | 340 |
| `Rubinstein_Opening` | 335 |
| `Ware_Defense` | 325 |
| `Blumenfeld_Countergambit` | 312 |
| `Goldsmith_Defense` | 307 |
| `Pseudo_Queens_Indian_Defense` | 294 |
| `Clemenz_Opening` | 284 |
| `Barnes_Defense` | 270 |
| `Paleface_Attack` | 257 |
| `Carr_Defense` | 244 |
| `Kangaroo_Defense` | 219 |
| `Gedults_Opening` | 194 |
| `Wade_Defense` | 183 |
| `Portuguese_Opening` | 181 |
| `Gunderam_Defense` | 172 |
| `Benko_Gambit_Declined` | 155 |
| `Amar_Opening` | 127 |
| `Lasker_Simul_Special` | 124 |
| `Amazon_Attack` | 115 |
| `Center_Game_Accepted` | 91 |
| `Semi-Slav_Defense_Accepted` | 89 |
| `Sodium_Attack` | 84 |
| `Robatsch_Defense` | 78 |
| `Kings_Pawn` | 75 |
| `Hippopotamus_Defense` | 68 |
| `Fried_Fox_Defense` | 67 |
| `Lemming_Defense` | 62 |
| `Creepy_Crawly_Formation` | 52 |
| `Valencia_Opening` | 52 |
| `London_System_with_Bd3` | 42 |
| `Polish_Opening_with_d5` | 39 |
| `English_Orangutan` | 27 |
| `Crab_Opening` | 26 |
| `Bongcloud_Attack` | 25 |
| `Blumenfeld_Countergambit_Accepted` | 23 |
| `Australian_Defense` | 23 |
| `Montevideo_Defense` | 22 |
| `Guatemala_Defense` | 22 |
| `Kings_Indian_Attack_with_e6` | 21 |
| `London_System_with_Be2` | 19 |
| `Vulture_Defense` | 18 |
| `Marienbad_System` | 14 |
| `Global_Opening` | 14 |
| `Dory_Defense` | 13 |
| `Bronstein_Gambit` | 12 |
| `System` | 12 |
| `Kings_Indian_Attack_with_Bf5` | 8 |
| `Zukertort_Defense` | 6 |
| `Irish_Gambit` | 5 |
| `Norwegian_Defense` | 4 |
| `Colle_System` | 3 |
| `Queens_Pawn_Mengarini_Attack` | 3 |
| `Borg_Opening` | 3 |
| `Zaire_Defense` | 2 |
| `Amsterdam_Attack` | 1 |

Variation tags are not listed -- there are 1,589 of them -- but they are all
this family name plus a suffix, so `--opening Sicilian_Defense_` with a
variation name works if you know it.

## How well-tested a puzzle is

```sh
./puzzle play --min-plays 1000
```

Puzzle ratings settle as more people attempt them, so a puzzle with a handful
of plays has a rating that is mostly guesswork. `--min-plays` filters on the
attempt count, which ranges from 0 to about 313,000.

## Choosing which puzzles come up

```sh
./puzzle play -n 25             # a longer session
./puzzle play --seed 42         # the same set again, in the same order
./puzzle play --id sAIXc        # one specific puzzle
./puzzle play --daily           # today's lichess puzzle
```

Without `--seed`, selection is random over everything matching. With one, the
same seed and the same filters give the same puzzles in the same order, which
is what you want for comparing yourself over time or re-running a set.

## In the data but not filterable

The index also stores each puzzle's popularity (a vote score from -83 to 100)
and its lichess game URL, and the solution's length is implied by the
`oneMove`/`short`/`long`/`veryLong` themes. None of those are exposed as
filters, nor is which colour you play. Say the word if any would be useful.
