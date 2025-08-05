# Football API
from espn_api.football import League
from flask import Flask, render_template
from collections import defaultdict
import os

app = Flask(__name__)

# Init
LEAGUE_ID = 284843139
ESPN_S2 = os.environ.get("ESPN_S2")
SWID = os.environ.get("SWID")

league = League(league_id=LEAGUE_ID, year=2021, espn_s2=ESPN_S2, swid=SWID)

@app.route('/')
def home():
    teams = sorted(league.teams, key=lambda x: x.standing)
    matchups = league.scoreboard()
    return render_template('index.html', teams=teams, matchups=matchups)

@app.route('/headtohead')
def head_to_head():
    seasons = range(2021, 2024)  # Adjust for your league's years
    head_to_head_records = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # wins, losses
    owner_id_to_name = {}
    owner_id_to_logo = {}

    for year in seasons:
        try:
            season_league = League(
                league_id=LEAGUE_ID,
                year=year,
                espn_s2=ESPN_S2,
                swid=SWID
            )
        except Exception as e:
            print(f"Error loading league for {year}: {e}")
            continue

        for week in range(1, 18):  # 17 weeks regular season max
            try:
                scoreboard = season_league.scoreboard(week)
            except:
                continue

            for matchup in scoreboard:
                home = matchup.home_team
                away = matchup.away_team

                if not home or not away:
                    continue

                # Get owner info safely
                def get_owner_info(team):
                    if team.owners and len(team.owners) > 0:
                        owner = team.owners[0]
                        return owner.get('id', 'unknown_id'), owner.get('displayName', 'Unknown')
                    return 'unknown_id', 'Unknown'

                # # Collect logos (use the most recent logo you find for the owner)
                home_id, home_name = get_owner_info(home)
                away_id, away_name = get_owner_info(away)
                # if home_id not in owner_id_to_logo and hasattr(home, 'logo'):
                #     owner_id_to_logo[home_id] = home.logo or ''
                # if away_id not in owner_id_to_logo and hasattr(away, 'logo'):
                #     owner_id_to_logo[away_id] = away.logo or ''

                # Save mapping for display
                owner_id_to_name[home_id] = home_name
                owner_id_to_name[away_id] = away_name

                home_score = matchup.home_score
                away_score = matchup.away_score

                if home_score > away_score:
                    head_to_head_records[home_id][away_id][0] += 1
                    head_to_head_records[away_id][home_id][1] += 1
                elif away_score > home_score:
                    head_to_head_records[away_id][home_id][0] += 1
                    head_to_head_records[home_id][away_id][1] += 1
                # ties ignored

    owner_ids = sorted(owner_id_to_name.keys(), key=lambda oid: owner_id_to_name[oid].lower())
    table = []

    for oid in owner_ids:
        row = {'owner_id': oid, 'owner_name': owner_id_to_name[oid], 'record': {}}
        for opponent_id in owner_ids:
            if opponent_id == oid:
                row['record'][opponent_id] = '—'
            else:
                wins, losses = head_to_head_records[oid][opponent_id]
                row['record'][opponent_id] = f'{wins}-{losses}'
        table.append(row)

    return render_template(
        'headtohead.html',
        table=table,
        owner_ids=owner_ids,
        owner_id_to_name=owner_id_to_name
    )

@app.route('/records')
def league_records():
    from statistics import mean

    seasons = range(2021, 2024)  # Adjust to your league's active years
    records = []

    for year in seasons:
        try:
            season_league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID)
        except Exception as e:
            print(f"Error loading league for {year}: {e}")
            continue

        highest_game = {'score': 0}
        lowest_game = {'score': float('inf')}
        season_scores = defaultdict(float)
        manager_efficiencies = defaultdict(list)

        for week in range(1, 18):
            try:
                scoreboard = season_league.scoreboard(week)
            except:
                continue

            for matchup in scoreboard:
                for team in [matchup.home_team, matchup.away_team]:
                    if not team:
                        continue

                    points = team.score
                    team_name = team.team_name
                    owners = team.owners
                    owner_name = owners[0]['displayName'] if owners else 'Unknown'

                    # Record game highs/lows
                    if points > highest_game['score']:
                        highest_game = {'score': points, 'team': team_name, 'owner': owner_name, 'week': week}
                    if points < lowest_game['score']:
                        lowest_game = {'score': points, 'team': team_name, 'owner': owner_name, 'week': week}

                    # Track season total
                    season_scores[owner_name] += points

                    # Manager rating (actual / possible)
                    if hasattr(team, 'lineup') and hasattr(team, 'bench'):
                        actual = sum(p.points for p in team.lineup if p and hasattr(p, 'points'))
                        bench = [p for p in team.bench if p and hasattr(p, 'points')]
                        total_pool = team.lineup + bench
                        max_possible = 0
                        used_slots = defaultdict(int)

                        for player in sorted(total_pool, key=lambda p: getattr(p, 'points', 0), reverse=True):
                            pos = player.position
                            # Roster limits for manager calc — simplified
                            max_starters = team.roster.get(pos, 0)
                            if used_slots[pos] < max_starters:
                                max_possible += player.points
                                used_slots[pos] += 1

                        if max_possible > 0:
                            efficiency = actual / max_possible
                            manager_efficiencies[owner_name].append(efficiency)

        # Calculate best and worst season scores
        if season_scores:
            max_points_owner = max(season_scores.items(), key=lambda x: x[1])
            min_points_owner = min(season_scores.items(), key=lambda x: x[1])
        else:
            max_points_owner = min_points_owner = ('N/A', 0)

        # Best manager efficiency (average over season)
        best_manager = ('N/A', 0)
        for owner, efficiencies in manager_efficiencies.items():
            avg = mean(efficiencies)
            if avg > best_manager[1]:
                best_manager = (owner, avg)

        records.append({
            'year': year,
            'highest_game': highest_game,
            'lowest_game': lowest_game,
            'most_points': max_points_owner,
            'least_points': min_points_owner,
            'best_manager': best_manager
        })

    return render_template('records.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)