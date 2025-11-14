# stats/management/commands/import_players.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from stats.models import Team, Player

import pandas as pd
import math
import re

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
NAME_KEYS = {
    "player", "players", "name", "player name", "full name"
}

def _clean_header(v):
    return str(v).strip().lower()

def as_float(v, default=0.0):
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return default
        if isinstance(v, str):
            v = v.strip().replace(",", ".")
        return float(v)
    except Exception:
        return default

def as_int(v, default=0):
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return default
        if isinstance(v, str):
            v = v.strip()
            if not re.fullmatch(r"-?\d+(\.\d+)?", v):
                return default
        return int(float(v))
    except Exception:
        return default

def norm_pos(v):
    if not v:
        return "Guard"
    v = str(v).strip().title()
    return v if v in {"Guard", "Forward", "Center"} else "Guard"

def pct01(v):
    """Normalize a percent into [0,1]. Accepts 61 -> 0.61, 0.61 -> 0.61."""
    f = as_float(v, 0.0)
    if f > 1.0:
        f = f / 100.0
    return max(0.0, min(1.0, f))

def pick(row, *cands):
    """Fetch value from a row using tolerant header matching."""
    lower = {str(k).strip().lower(): k for k in row.index}
    for c in cands:
        key = str(c).strip().lower()
        if key in lower:
            return row[lower[key]]
    return None

def find_header_row(df):
    """
    Detect which row contains the actual column headers
    by scanning first ~10 rows for something that looks like a name column.
    """
    max_check = min(10, len(df))
    for i in range(max_check):
        headers = [_clean_header(x) for x in df.iloc[i].values]
        if any(h in NAME_KEYS for h in headers):
            return i
    return 0

# ------------------------------------------------------------
# Command
# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Import teams & players from an Excel workbook (one sheet per team)."

    def add_arguments(self, parser):
        parser.add_argument("xlsx_path", type=str, help="Path to Excel file")
        parser.add_argument("--reset", action="store_true",
                            help="Delete existing Players before import")
        parser.add_argument("--debug", action="store_true",
                            help="Print detected header row and columns per sheet")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["xlsx_path"]
        try:
            raw_book = pd.read_excel(path, sheet_name=None, header=None, engine="openpyxl")
        except Exception as e:
            raise CommandError(f"Failed to read Excel: {e}")

        if opts["reset"]:
            self.stdout.write(self.style.WARNING("Deleting ALL existing players..."))
            Player.objects.all().delete()

        total_players = 0

        for sheet_name, raw_df in raw_book.items():
            hdr_idx = find_header_row(raw_df)
            df = pd.read_excel(path, sheet_name=sheet_name, header=hdr_idx, engine="openpyxl")
            # drop "Unnamed: ..." auto-index columns
            df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
            headers_norm = [_clean_header(c) for c in df.columns]

            if opts["debug"]:
                self.stdout.write(self.style.NOTICE(
                    f"[{sheet_name}] header row={hdr_idx} | columns={list(df.columns)}"
                ))

            team, _ = Team.objects.get_or_create(name=str(sheet_name).strip())

            # ensure we really have a name column
            if not any(h in NAME_KEYS for h in headers_norm):
                self.stdout.write(self.style.WARNING(
                    f"[{team.name}] skipped: no 'Player/Players/Name' column found."
                ))
                continue

            # remove empty-name rows
            name_series = None
            for k in ("Player", "Players", "Name", "Player Name", "Full Name"):
                if k in df.columns:
                    name_series = df[k]
                    break
            if name_series is not None:
                df = df[name_series.notna()]

            created_here = 0
            for _, row in df.iterrows():
                # --- identity ---
                name = pick(row, "Player", "Players", "Name", "Player Name", "Full Name")
                if not name or (isinstance(name, float) and math.isnan(name)):
                    continue
                name = str(name).strip()

                number    = as_int(pick(row, "Number", "#", "No"))
                position  = norm_pos(pick(row, "Position", "Pos"))

                # --- core stats ---
                games     = as_int(pick(row, "Games", "GP"))
                minutes   = as_float(pick(row, "Minutes per game", "Min", "MIN", "Minutes"))

                pts       = as_float(pick(row, "Points per game", "PTS", "PPG"))
                reb       = as_float(pick(row, "Rebounds per game", "REB", "RPG"))
                ast       = as_float(pick(row, "Assists per game", "AST", "APG"))
                stl       = as_float(pick(row, "Steals per game", "STL", "SPG"))
                blk       = as_float(pick(row, "Blocks per game", "BLK", "BPG"))
                rating    = as_float(pick(row, "Rating", "Eff", "EFF"))

                fouls     = as_float(pick(row, "Fouls per game", "Fouls"))
                tov       = as_float(pick(row, "Turnovers per game", "Turnovers", "TOV"))

                two_pct   = pct01(pick(row, "2 points %", "2PT%", "2PT %", "Two Points %"))
                three_pct = pct01(pick(row, "3 points %", "3PT%", "3PT %", "Three Points %"))

                Player.objects.create(
                    team=team,
                    name=name,
                    number=number,
                    position=position,
                    games=games,
                    minutes_per_game=minutes,
                    points_per_game=pts,
                    rebounds_per_game=reb,
                    assists_per_game=ast,
                    steals_per_game=stl,
                    blocks_per_game=blk,
                    rating=rating,
                    fouls_per_game=fouls,
                    turnovers_per_game=tov,
                    two_points_pct=two_pct,
                    three_points_pct=three_pct,
                )
                created_here += 1
                total_players += 1

            self.stdout.write(self.style.SUCCESS(f"[{team.name}] imported {created_here} players."))

        self.stdout.write(self.style.SUCCESS(f"Done. Total players imported: {total_players}"))
