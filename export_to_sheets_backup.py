import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from espn_api.football import League
import gspread
from gspread.utils import rowcol_to_a1, a1_to_rowcol
from google.oauth2.service_account import Credentials
from typing import List

load_dotenv()

LEAGUE_ID = 284843139
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
GOOGLE_CREDS = json.loads(os.getenv("GOOGLE_CREDS"))
SEASON_YEAR = 2023
SEASONS = [2021,2022,2023]
SEASON_WEEKS = 17
SHEET_NAME = "Fantasy Football Records"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(GOOGLE_CREDS, scopes=scope)
gc = gspread.authorize(credentials)

# Open or create the spreadsheet
try:
    sh = gc.open(SHEET_NAME)
except gspread.SpreadsheetNotFound:
    sh = gc.create(SHEET_NAME)

# Your helper function
def batch_update(worksheet, start_cell: str, data: List[List], col_labels: List[str] = None):
    """
    Writes a block of data to a worksheet starting at start_cell (e.g., "A2").
    Optionally includes column labels above the data block.
    """
    start_row, start_col = a1_to_rowcol(start_cell)

    if col_labels:
        worksheet.update(rowcol_to_a1(start_row, start_col), [col_labels])
        start_row += 1  # Push data block down one row

    if not data:
        return

    num_rows = len(data)
    num_cols = len(data[0]) if data else 1

    end_col = start_col + num_cols - 1
    end_row = start_row + num_rows - 1

    range_label = f"{rowcol_to_a1(start_row, start_col)}:{rowcol_to_a1(end_row, end_col)}"
    worksheet.update(range_label, data)

def get_league(year=SEASON_YEAR):
    return League(
        league_id=LEAGUE_ID,
        year=year,
        espn_s2=ESPN_S2,
        swid=SWID
    )


def write_records_tab(records_data):
    try:
        worksheet = sh.worksheet("Records")
        sh.del_worksheet(worksheet)
    except gspread.exceptions.WorksheetNotFound:
        pass
    worksheet = sh.add_worksheet(title="Records", rows="100", cols="10")
    worksheet.clear()

    row_idx = 1

    # Section 1: Most / Least Points Game & Season
    worksheet.update(f"A{row_idx}", [["🏆 Most / Least Points in Game & Season"]])
    row_idx += 1
    worksheet.update(f"A{row_idx}", [["Category", "Owner", "Team", "Points", "Year", "Week"]])
    row_idx += 1

    categories = [
        "Most Points Game",
        "Least Points Game",
        "Most Points Season",
        "Least Points Season",
    ]

    batch_data = []
    for cat in categories:
        rec = records_data.get(cat, {})
        batch_data.append([
            cat,
            rec.get("owner", ""),
            rec.get("team", ""),
            rec.get("points", ""),
            rec.get("year", ""),
            rec.get("week", "")
        ])

    batch_update(worksheet, f"A{row_idx}", batch_data)
    row_idx += len(batch_data)

    row_idx += 1  # spacer

    # Section 2: Largest / Smallest Point Differential
    worksheet.update(f"A{row_idx}", [["📊 Largest / Smallest Point Differentials in a Game"]])
    row_idx += 1
    worksheet.update(f"A{row_idx}",
                     [["Category", "Winner", "Loser", "Winner Team", "Loser Team", "Point Diff", "Year", "Week"]])
    row_idx += 1

    batch_data = []
    for cat in ["Largest Point Differential", "Smallest Point Differential"]:
        rec = records_data.get(cat, {})
        batch_data.append([
            cat,
            rec.get("winner_owner", ""),
            rec.get("loser_owner", ""),
            rec.get("winner_team", ""),
            rec.get("loser_team", ""),
            rec.get("point_diff", ""),
            rec.get("year", ""),
            rec.get("week", "")
        ])

    batch_update(worksheet, f"A{row_idx}", batch_data)
    row_idx += len(batch_data)

    row_idx += 1  # spacer

    # Section 3: The Managing Maestro
    worksheet.update(f"A{row_idx}", [["🎯 The Managing Maestro (Season Efficiency)"]])
    row_idx += 1
    worksheet.update(f"A{row_idx}", [["Owner", "Team", "Efficiency (Starters / Max Possible)", "Year"]])
    row_idx += 1

    maestro = records_data.get("The Managing Maestro", {})
    worksheet.update(f"A{row_idx}", [[
        maestro.get("owner", ""),
        maestro.get("team", ""),
        maestro.get("efficiency", ""),
        maestro.get("year", "")
    ]])
    row_idx += 2  # space

    # Section 4: The Hustler & The Zen Master (FA Pickups)
    worksheet.update(f"A{row_idx}", [["⚡ The Hustler (Most Free Agent Pickups) & 🧘 The Zen Master (Fewest Free Agent Pickups)"]])
    row_idx += 1
    worksheet.update(f"A{row_idx}", [["Award", "Owner", "Team", "Pickups", "Year"]])
    row_idx += 1

    hustler = records_data.get("Most Free Agent Pickups", {})
    zenmaster = records_data.get("Fewest Free Agent Pickups", {})

    worksheet.update(f"A{row_idx}", [[
        "The Hustler",
        hustler.get("owner", ""),
        hustler.get("team", ""),
        hustler.get("pickups", ""),
        hustler.get("year", "")
    ]])
    row_idx += 1
    worksheet.update(f"A{row_idx}", [[
        "The Zen Master",
        zenmaster.get("owner", ""),
        zenmaster.get("team", ""),
        zenmaster.get("pickups", ""),
        zenmaster.get("year", "")
    ]])
    row_idx += 2  # spacer

    # Section 5: The Loyalist
    worksheet.update(f"A{row_idx}", [["🏅 The Loyalist"]])
    row_idx += 1
    worksheet.update(f"A{row_idx}", [[
        "This award goes to the manager who retained the most players from their original draft roster throughout the season."
    ]])
    row_idx += 1
    worksheet.update(f"A{row_idx}", [["Owner", "Team", "Players Retained", "Year"]])
    row_idx += 1

    loyalist = records_data.get("The Loyalist", {})
    worksheet.update(f"A{row_idx}", [[
        loyalist.get("owner", ""),
        loyalist.get("team", ""),
        loyalist.get("players_retained", ""),
        loyalist.get("year", "")
    ]])

def write_current_season_tab():
    try:
        worksheet = sh.worksheet("Current Season")
        sh.del_worksheet(worksheet)
    except gspread.exceptions.WorksheetNotFound:
        pass
    worksheet = sh.add_worksheet(title="Current Season", rows="100", cols="10")
    worksheet.clear()

    league = get_league(SEASON_YEAR)
    teams = sorted(league.teams, key=lambda t: t.standing)
    row_idx = 1

    # Standings
    worksheet.update(f"A{row_idx}", [["🏆 Current Standings"]])
    row_idx += 1

    standings_data = []
    for team in teams:
        owner = team.owners[0]['displayName'] if team.owners else 'Unknown'
        standings_data.append([
            team.standing,
            team.team_name,
            owner,
            team.wins,
            team.losses,
            round(team.points_for, 2),
            round(team.points_against, 2)
        ])

    batch_update(worksheet, f"A{row_idx}", standings_data, col_labels=[
        "Rank", "Team", "Owner", "Wins", "Losses", "Points For", "Points Against"
    ])
    row_idx += len(standings_data) + 2  # leave a spacer row

    # Remaining schedule
    worksheet.update(f"A{row_idx}", [["📅 Upcoming Schedule"]])
    row_idx += 1
    current_week = league.current_week
    schedule_data = []
    for week in range(current_week, SEASON_WEEKS + 1):
        try:
            matchups = league.scoreboard(week)
        except Exception:
            continue
        for matchup in matchups:
            home = matchup.home_team.team_name if matchup.home_team else "TBD"
            away = matchup.away_team.team_name if matchup.away_team else "TBD"
            schedule_data.append([week, f"{home} vs {away}"])

    batch_update(worksheet, f"A{row_idx}", schedule_data, col_labels=["Week", "Matchup"])
    row_idx += len(schedule_data)

def write_headtohead_tab():
    try:
        worksheet = sh.worksheet("Head-to-Head")
        sh.del_worksheet(worksheet)
    except gspread.exceptions.WorksheetNotFound:
        pass
    worksheet = sh.add_worksheet(title="Head-to-Head", rows="100", cols="50")
    worksheet.clear()

    # SEASONS = [2021,2022,2023]  # 3 SEASONS: 2023, 2024, 2025 (adjust as needed)
    head_to_head_records = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    owner_id_to_name = {}

    for year in SEASONS:
        try:
            league = get_league(year)
        except Exception as e:
            print(f"Error loading league for {year}: {e}")
            continue

        for week in range(1, SEASON_WEEKS + 1):
            try:
                scoreboard = league.scoreboard(week)
            except Exception:
                continue
            for matchup in scoreboard:
                home = matchup.home_team
                away = matchup.away_team
                if not home or not away:
                    continue

                # owner info
                home_owner_id = home.owners[0]['id'] if home.owners else "unknown"
                away_owner_id = away.owners[0]['id'] if away.owners else "unknown"
                home_owner_name = home.owners[0]['displayName'] if home.owners else "Unknown"
                away_owner_name = away.owners[0]['displayName'] if away.owners else "Unknown"

                owner_id_to_name[home_owner_id] = home_owner_name
                owner_id_to_name[away_owner_id] = away_owner_name

                home_score = matchup.home_score
                away_score = matchup.away_score

                if home_score > away_score:
                    head_to_head_records[home_owner_id][away_owner_id][0] += 1
                    head_to_head_records[away_owner_id][home_owner_id][1] += 1
                elif away_score > home_score:
                    head_to_head_records[away_owner_id][home_owner_id][0] += 1
                    head_to_head_records[home_owner_id][away_owner_id][1] += 1

    owner_ids = sorted(owner_id_to_name.keys(), key=lambda oid: owner_id_to_name[oid].lower())
    # Write matrix header
    print("owner_ids:", owner_ids)
    print("owner_id_to_name:", owner_id_to_name)
    print("Mapped names:", [owner_id_to_name.get(oid, "Unknown") for oid in owner_ids])
    worksheet.update("B1", [[owner_id_to_name.get(oid, "Unknown") for oid in owner_ids]])
    worksheet.update("A2", [[owner_id_to_name.get(oid, "Unknown")] for oid in owner_ids])

    # Write matrix body
    head_to_head_data = []

    for oid in owner_ids:
        row = []
        for oid2 in owner_ids:
            if oid == oid2:
                row.append("—")
            else:
                w, l = head_to_head_records[oid][oid2]
                row.append(f"{w}-{l}")
        head_to_head_data.append(row)

    # Write header row (owner names)
    worksheet.update("B1", [owner_ids])

    # Write owner names vertically in column A (from A2 down)
    worksheet.update("A2", [[owner_id_to_name[oid]] for oid in owner_ids])

    # Batch write the matrix starting at B2
    batch_update(worksheet, "B2", head_to_head_data)

def calculate_records():
    records = {}

    most_points_game = {"points": -1}
    least_points_game = {"points": 99999}
    most_points_season = defaultdict(lambda: 0)  # owner_id: points
    least_points_season = defaultdict(lambda: 999999)
    largest_point_diff = {"diff": -1}
    smallest_point_diff = {"diff": 99999}
    managing_maestro = {"efficiency": -1}
    free_agent_pickups = defaultdict(int)  # owner_id: count
    total_pickups = defaultdict(int)
    loyalist_players = defaultdict(lambda: defaultdict(int))  # year -> owner_id -> count of draft players retained
    owner_id_to_name = {}
    owner_id_to_team_name = {}

    for year in SEASONS:
        league = get_league(year)
        for team in league.teams:
            # owner info
            owner = team.owners[0] if team.owners else {"id": "unknown", "displayName": "Unknown"}
            owner_id = owner.get("id", "unknown")
            owner_name = owner.get("displayName", "Unknown")
            owner_id_to_name[owner_id] = owner_name
            owner_id_to_team_name[owner_id] = team.team_name

            # Season points tally
            points = team.points_for
            if points > most_points_season[owner_id]:
                most_points_season[owner_id] = points
            if points < least_points_season[owner_id]:
                least_points_season[owner_id] = points

            # Free agent pickups
            free_agent_pickups[owner_id] += getattr(team, 'free_agent_acquisitions', 0)

            # Loyalist: count how many draft players still on roster
            draft_player_ids = {p.playerId for p in team.draft_results} if hasattr(team, 'draft_results') else set()
            roster_player_ids = {p.playerId for p in team.roster} if hasattr(team, 'roster') else set()
            retained = len(draft_player_ids.intersection(roster_player_ids))
            loyalist_players[year][owner_id] = retained

        # Check each week for points and point differentials
        for week in range(1, SEASON_WEEKS + 1):
            try:
                scoreboard = league.scoreboard(week)
            except Exception:
                continue

            for matchup in scoreboard:
                home = matchup.home_team
                away = matchup.away_team
                if not home or not away:
                    continue

                home_score = matchup.home_score
                away_score = matchup.away_score

                # Most/Least points in a game
                if home_score > most_points_game.get("points", -1):
                    most_points_game.update({
                        "owner": home.owners[0]['displayName'] if home.owners else "Unknown",
                        "team": home.team_name,
                        "points": home_score,
                        "year": year,
                        "week": week
                    })
                if away_score > most_points_game.get("points", -1):
                    most_points_game.update({
                        "owner": away.owners[0]['displayName'] if away.owners else "Unknown",
                        "team": away.team_name,
                        "points": away_score,
                        "year": year,
                        "week": week
                    })

                if home_score < least_points_game.get("points", 99999):
                    least_points_game.update({
                        "owner": home.owners[0]['displayName'] if home.owners else "Unknown",
                        "team": home.team_name,
                        "points": home_score,
                        "year": year,
                        "week": week
                    })
                if away_score < least_points_game.get("points", 99999):
                    least_points_game.update({
                        "owner": away.owners[0]['displayName'] if away.owners else "Unknown",
                        "team": away.team_name,
                        "points": away_score,
                        "year": year,
                        "week": week
                    })

                # Point differentials
                diff1 = abs(home_score - away_score)
                diff2 = diff1
                if diff1 > largest_point_diff.get("diff", -1):
                    largest_point_diff.update({
                        "winner_owner": (home.owners[0]['displayName'] if home_score > away_score and home.owners else
                                         away.owners[0]['displayName'] if away.owners else "Unknown"),
                        "loser_owner": (away.owners[0]['displayName'] if home_score > away_score and away.owners else
                                        home.owners[0]['displayName'] if home.owners else "Unknown"),
                        "winner_team": home.team_name if home_score > away_score else away.team_name,
                        "loser_team": away.team_name if home_score > away_score else home.team_name,
                        "point_diff": diff1,
                        "year": year,
                        "week": week
                    })
                if diff2 < smallest_point_diff.get("diff", 99999) and diff2 != 0:
                    smallest_point_diff.update({
                        "winner_owner": (home.owners[0]['displayName'] if home_score > away_score and home.owners else
                                         away.owners[0]['displayName'] if away.owners else "Unknown"),
                        "loser_owner": (away.owners[0]['displayName'] if home_score > away_score and away.owners else
                                        home.owners[0]['displayName'] if home.owners else "Unknown"),
                        "winner_team": home.team_name if home_score > away_score else away.team_name,
                        "loser_team": away.team_name if home_score > away_score else home.team_name,
                        "point_diff": diff2,
                        "year": year,
                        "week": week
                    })

        # Calculate Managing Maestro efficiency: season starter points / max possible starter points
        total_efficiency_by_owner = defaultdict(lambda: {"starter_points": 0, "max_points": 0})

        for week in range(1, SEASON_WEEKS + 1):
            try:
                scoreboard = league.scoreboard(week)
            except Exception:
                continue

            for matchup in scoreboard:
                for team in [matchup.home_team, matchup.away_team]:
                    if not team:
                        continue
                    owner = team.owners[0]['id'] if team.owners else "unknown"
                    # sum weekly starter points and max points possible for that team
                    starter_points = getattr(team, 'starter_points', None)
                    max_points = getattr(team, 'max_points', None)

                    # fallback: calculate from starters and bench if attributes missing
                    if starter_points is None or max_points is None:
                        # Sum points from starters
                        try:
                            starter_points = sum(p.points for p in team.starters if hasattr(p, 'points'))
                            bench_points = sum(p.points for p in team.bench if hasattr(p, 'points'))
                            max_points = starter_points + bench_points
                        except Exception:
                            starter_points = 0
                            max_points = 0

                    total_efficiency_by_owner[owner]["starter_points"] += starter_points or 0
                    total_efficiency_by_owner[owner]["max_points"] += max_points or 0

        for owner_id, vals in total_efficiency_by_owner.items():
            max_p = vals["max_points"]
            if max_p > 0:
                efficiency = vals["starter_points"] / max_p
                if efficiency > managing_maestro["efficiency"]:
                    print(f"Owner: {owner_id_to_name.get(owner_id, "Unknown")}, Starting: {vals["starter_points"]}, MaxPossible: {max_p}")

                    managing_maestro.update({
                        "owner": owner_id_to_name.get(owner_id, "Unknown"),
                        "team": owner_id_to_team_name.get(owner_id, ""),
                        "efficiency": round(efficiency, 4),
                        "year": year
                    })

    # Finalize Most/Least points season
    most_points_season_owner = max(most_points_season, key=most_points_season.get, default=None)
    least_points_season_owner = min(least_points_season, key=least_points_season.get, default=None)

    records.update({
        "Most Points Game": most_points_game,
        "Least Points Game": least_points_game,
        "Most Points Season": {
            "owner": owner_id_to_name.get(most_points_season_owner, ""),
            "team": owner_id_to_team_name.get(most_points_season_owner, ""),
            "points": most_points_season.get(most_points_season_owner, ""),
            "year": year,
            "week": ""
        },
        "Least Points Season": {
            "owner": owner_id_to_name.get(least_points_season_owner, ""),
            "team": owner_id_to_team_name.get(least_points_season_owner, ""),
            "points": least_points_season.get(least_points_season_owner, ""),
            "year": year,
            "week": ""
        },
        "Largest Point Differential": largest_point_diff,
        "Smallest Point Differential": smallest_point_diff,
        "The Managing Maestro": managing_maestro,
        "Most Free Agent Pickups": {
            "owner": "",
            "team": "",
            "pickups": 0,
            "year": year
        },
        "Fewest Free Agent Pickups": {
            "owner": "",
            "team": "",
            "pickups": 999999,
            "year": year
        },
        "The Loyalist": {
            "owner": "",
            "team": "",
            "players_retained": 0,
            "year": year
        }
    })

    # Find Most / Fewest free agent pickups (season 2025 only)
    for owner_id, pickups in free_agent_pickups.items():
        if pickups > records["Most Free Agent Pickups"]["pickups"]:
            records["Most Free Agent Pickups"].update({
                "owner": owner_id_to_name.get(owner_id, ""),
                "team": owner_id_to_team_name.get(owner_id, ""),
                "pickups": pickups,
                "year": SEASON_YEAR
            })
        if pickups < records["Fewest Free Agent Pickups"]["pickups"]:
            records["Fewest Free Agent Pickups"].update({
                "owner": owner_id_to_name.get(owner_id, ""),
                "team": owner_id_to_team_name.get(owner_id, ""),
                "pickups": pickups,
                "year": SEASON_YEAR
            })

    # Loyalist - max retained draft players (season 2025 only)
    loyalist_counts = loyalist_players.get(SEASON_YEAR, {})
    if loyalist_counts:
        max_retained_owner = max(loyalist_counts, key=loyalist_counts.get)
        records["The Loyalist"].update({
            "owner": owner_id_to_name.get(max_retained_owner, ""),
            "team": owner_id_to_team_name.get(max_retained_owner, ""),
            "players_retained": loyalist_counts[max_retained_owner],
            "year": SEASON_YEAR
        })

    return records

def main():
    print("Gathering records data...")
    records_data = calculate_records()
    print("Writing Current Season tab...")
    write_current_season_tab()
    print("Writing Head-to-Head tab...")
    write_headtohead_tab()
    print("Writing Records tab...")
    write_records_tab(records_data)
    print("Done!")

if __name__ == "__main__":
    main()