# Football API
from espn_api.football import League
from flask import Flask, render_template
from collections import defaultdict

app = Flask(__name__)


# Init
LEAGUE_ID = 284843139
ESPN_S2 = 'AEBPqnCavi8uTOeX%2Frgs4bun132KT9Ahi886jtxPhG8GfUqKxMbvcmAsrpQkcHSlcxdkuQOEP%2BYAuoedujiN726GYLDPwMRSS86IfNLVMpMsg3RxlDN0GnW5l4r7MxJBs8zcVc6URrqzkDeU6dDh0kbP6CuwwGmrYHWKzN%2FZsd2H%2FvTQZw2lafEotomG0rLHJqNC0lD%2BYh6IO3rtPdwouQeWoeGYYS9ah1XkhMlxn4H4C6IL1UZyWT5ofF%2BoL1EspfKOx%2FJ%2Ff3PtIanfbSbYoZC8Nw1x5WHw8STgCTglPa%2FOTA%3D%3D'
SWID = '{A466BE55-1746-4478-A6BE-551746D478A4}'
league = League(league_id=LEAGUE_ID, year=2021, espn_s2=ESPN_S2, swid=SWID)

# print(league.standings())

# print(league.power_rankings(week = 1))


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

if __name__ == '__main__':
    app.run(debug=True)