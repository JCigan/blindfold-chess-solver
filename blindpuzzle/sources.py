"""Where puzzles come from: the lichess API, or the local puzzle database.

The API needs no setup but cannot filter by rating range. Lichess exposes
only a difficulty relative to your own puzzle rating, and only when
authenticated, so rating ranges require the downloaded database.
"""

from __future__ import annotations

import csv
import io
import os
import sqlite3
import sys
import time
import warnings
from collections import Counter
from typing import Iterator, List, Optional, Sequence

from .model import Puzzle

DB_URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
USER_AGENT = "blindpuzzle/1.0 (personal blindfold trainer)"

# macOS ships LibreSSL, which makes urllib3 warn on import.
warnings.filterwarnings("ignore", message=".*OpenSSL.*")


def data_dir() -> str:
    override = os.environ.get("BLINDPUZZLE_DIR")
    if override:
        path = os.path.expanduser(override)
    else:
        path = os.path.expanduser("~/.local/share/blindpuzzle")
    os.makedirs(path, exist_ok=True)
    return path


def archive_path() -> str:
    return os.path.join(data_dir(), "lichess_db_puzzle.csv.zst")


def db_path() -> str:
    return os.path.join(data_dir(), "puzzles.sqlite")


def have_local_db() -> bool:
    return os.path.exists(db_path())


# --------------------------------------------------------------------------
# API source
# --------------------------------------------------------------------------

class LichessApi:
    BASE = "https://lichess.org/api/puzzle"

    def __init__(self, timeout: int = 20):
        import requests  # imported lazily so db-only use needs no network stack

        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.timeout = timeout

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        for attempt in range(4):
            response = self.session.get(
                "{}/{}".format(self.BASE, path), params=params, timeout=self.timeout
            )
            if response.status_code == 429:
                wait = 8 * (attempt + 1)
                print("  lichess rate limit hit; waiting {}s...".format(wait), file=sys.stderr)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        raise RuntimeError("lichess API kept rate limiting us; try again later")

    def by_id(self, puzzle_id: str) -> Puzzle:
        return Puzzle.from_api(self._get(puzzle_id))

    def daily(self) -> Puzzle:
        return Puzzle.from_api(self._get("daily"))

    def next(self, theme: Optional[str] = None) -> Puzzle:
        params = {"angle": theme} if theme else None
        return Puzzle.from_api(self._get("next", params))

    def stream(self, theme: Optional[str] = None, count: int = 10) -> Iterator[Puzzle]:
        """The API has no unauthenticated batch endpoint, so poll one at a time."""
        seen = set()
        misses = 0
        while len(seen) < count and misses < 10:
            puzzle = self.next(theme)
            if puzzle.id in seen:
                misses += 1
                time.sleep(1.0)
                continue
            seen.add(puzzle.id)
            yield puzzle
            time.sleep(0.7)


# --------------------------------------------------------------------------
# Local database
# --------------------------------------------------------------------------

def download(force: bool = False, url: str = DB_URL) -> str:
    import requests

    dest = archive_path()
    if os.path.exists(dest) and not force:
        size = os.path.getsize(dest) / 1e6
        print("Already downloaded: {} ({:.0f} MB)".format(dest, size))
        print("Use --force to re-download.")
        return dest

    tmp = dest + ".part"
    print("Downloading {}".format(url))
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": USER_AGENT}) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        done = 0
        last_report = 0.0
        with open(tmp, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 20):
                handle.write(chunk)
                done += len(chunk)
                if done - last_report > 10e6:
                    last_report = done
                    if total:
                        print("\r  {:.0f} / {:.0f} MB ({:.0f}%)".format(
                            done / 1e6, total / 1e6, 100 * done / total), end="", flush=True)
                    else:
                        print("\r  {:.0f} MB".format(done / 1e6), end="", flush=True)
    print("\r  {:.0f} MB downloaded.{}".format(done / 1e6, " " * 20))
    os.replace(tmp, dest)
    return dest


def _csv_rows(path: str) -> Iterator[dict]:
    """Stream-decompress the .zst archive and yield CSV rows as dicts."""
    import zstandard

    decompressor = zstandard.ZstdDecompressor()
    with open(path, "rb") as raw:
        with decompressor.stream_reader(raw) as stream:
            text = io.TextIOWrapper(stream, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            try:
                for row in reader:
                    yield row
            except zstandard.ZstdError as exc:
                # A truncated archive (interrupted download) still yields every
                # complete row before the cut; say so rather than dying silently.
                print("\n  warning: archive ended early ({}); indexed what was readable".format(exc),
                      file=sys.stderr)


SCHEMA = """
CREATE TABLE IF NOT EXISTS puzzles (
    id         TEXT PRIMARY KEY,
    fen        TEXT NOT NULL,
    moves      TEXT NOT NULL,
    rating     INTEGER NOT NULL,
    popularity INTEGER,
    plays      INTEGER,
    themes     TEXT,
    openings   TEXT
);
CREATE TABLE IF NOT EXISTS theme_counts (theme TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def build_index(limit: Optional[int] = None, source: Optional[str] = None) -> str:
    archive = source or archive_path()
    if not os.path.exists(archive):
        raise SystemExit(
            "No puzzle archive at {}.\nRun:  ./puzzle fetch".format(archive)
        )

    target = db_path()
    tmp = target + ".building"
    if os.path.exists(tmp):
        os.remove(tmp)

    connection = sqlite3.connect(tmp)
    connection.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    connection.executescript(SCHEMA)

    themes = Counter()
    batch = []
    total = 0
    started = time.time()
    print("Indexing {} -> {}".format(archive, target))

    for row in _csv_rows(archive):
        try:
            rating = int(row["Rating"])
        except (TypeError, ValueError, KeyError):
            continue
        row_themes = (row.get("Themes") or "").split()
        themes.update(row_themes)
        batch.append((
            row["PuzzleId"], row["FEN"], row["Moves"], rating,
            _safe_int(row.get("Popularity")), _safe_int(row.get("NbPlays")),
            " ".join(row_themes), (row.get("OpeningTags") or "").strip(),
        ))
        total += 1
        if len(batch) >= 20000:
            connection.executemany(
                "INSERT OR REPLACE INTO puzzles VALUES (?,?,?,?,?,?,?,?)", batch)
            batch.clear()
            print("\r  {:,} puzzles...".format(total), end="", flush=True)
        if limit and total >= limit:
            break

    if batch:
        connection.executemany("INSERT OR REPLACE INTO puzzles VALUES (?,?,?,?,?,?,?,?)", batch)

    connection.executemany("INSERT OR REPLACE INTO theme_counts VALUES (?,?)", themes.items())
    connection.execute("INSERT OR REPLACE INTO meta VALUES ('count', ?)", (str(total),))
    connection.execute("INSERT OR REPLACE INTO meta VALUES ('built', ?)",
                       (time.strftime("%Y-%m-%d %H:%M"),))
    print("\r  {:,} puzzles indexed. Building index...".format(total))
    # Covering index: themes rides along in the index, so a rating+theme filter
    # never reads the table for candidates that fail the theme test. A plain
    # An index on rating alone cost ~465k random row reads, 18s on a cold
    # cache. rating leads here, so this serves rating-only queries too; a
    # separate rating index is redundant and misleads the query planner.
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_rating_themes ON puzzles(rating, themes)")
    # Without stats the planner ignores the covering index entirely.
    print("  Analysing...")
    connection.execute("ANALYZE")
    connection.commit()
    connection.close()
    os.replace(tmp, target)
    print("Done in {:.0f}s -> {} ({:.0f} MB)".format(
        time.time() - started, target, os.path.getsize(target) / 1e6))
    print("You can delete the archive now if you want the space back: {}".format(archive))
    return target


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _connect() -> sqlite3.Connection:
    path = db_path()
    if not os.path.exists(path):
        raise SystemExit(
            "No local puzzle database.\n"
            "Run:  ./puzzle fetch && ./puzzle index\n"
            "Or play straight from the API with:  ./puzzle play --source api"
        )
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def query(
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    themes: Sequence[str] = (),
    match_any: bool = False,
    opening: Optional[str] = None,
    min_plays: Optional[int] = None,
    count: int = 10,
    seed: Optional[int] = None,
) -> List[Puzzle]:
    clauses = []
    params: List = []
    if min_rating is not None:
        clauses.append("rating >= ?")
        params.append(min_rating)
    if max_rating is not None:
        clauses.append("rating <= ?")
        params.append(max_rating)
    if min_plays is not None:
        clauses.append("plays >= ?")
        params.append(min_plays)
    if themes:
        joiner = " OR " if match_any else " AND "
        theme_clause = joiner.join(["(' ' || themes || ' ') LIKE ?"] * len(themes))
        clauses.append("(" + theme_clause + ")")
        params.extend("% {} %".format(t) for t in themes)
    if opening:
        # Substring, not whole-tag: tags look like "Sicilian_Defense
        # Sicilian_Defense_Najdorf_Variation", so a bare "Sicilian" should
        # catch the whole family rather than nothing at all.
        clauses.append("openings LIKE ?")
        params.append("%{}%".format(opening))

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""

    if seed is None:
        order = "RANDOM()"
    else:
        # SQL RANDOM() ignores any seed, so scramble the rowid deterministically
        # instead: same seed and filters => same puzzles, same order, every run.
        # rowid follows insertion (i.e. puzzle id) order, which is uncorrelated
        # with rating or theme, so this shuffles rather than biases.
        order = "((rowid * 2654435761) + {}) % 4294967291".format(int(seed))

    sql = "SELECT * FROM puzzles{} ORDER BY {} LIMIT ?".format(where, order)
    params.append(count)

    connection = _connect()
    try:
        rows = connection.execute(sql, params).fetchall()
    finally:
        connection.close()

    return [Puzzle.from_db_row(row) for row in rows]


def theme_counts(top: Optional[int] = None) -> List[tuple]:
    connection = _connect()
    try:
        rows = connection.execute(
            "SELECT theme, n FROM theme_counts ORDER BY n DESC").fetchall()
    finally:
        connection.close()
    pairs = [(r["theme"], r["n"]) for r in rows]
    return pairs[:top] if top else pairs


def db_stats() -> dict:
    connection = _connect()
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta").fetchall())
        row = connection.execute(
            "SELECT MIN(rating) lo, MAX(rating) hi, COUNT(*) n FROM puzzles").fetchone()
    finally:
        connection.close()
    return {"count": row["n"], "min_rating": row["lo"], "max_rating": row["hi"],
            "built": meta.get("built", "unknown")}
