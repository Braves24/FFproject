# Football API
from espn_api.football import League
from flask import Flask, render_template
from collections import defaultdict

app_2 = Flask(__name__)


# Init
LEAGUE_ID = 284843139
ESPN_S2 = 'AEBPqnCavi8uTOeX%2Frgs4bun132KT9Ahi886jtxPhG8GfUqKxMbvcmAsrpQkcHSlcxdkuQOEP%2BYAuoedujiN726GYLDPwMRSS86IfNLVMpMsg3RxlDN0GnW5l4r7MxJBs8zcVc6URrqzkDeU6dDh0kbP6CuwwGmrYHWKzN%2FZsd2H%2FvTQZw2lafEotomG0rLHJqNC0lD%2BYh6IO3rtPdwouQeWoeGYYS9ah1XkhMlxn4H4C6IL1UZyWT5ofF%2BoL1EspfKOx%2FJ%2Ff3PtIanfbSbYoZC8Nw1x5WHw8STgCTglPa%2FOTA%3D%3D'
SWID = '{A466BE55-1746-4478-A6BE-551746D478A4}'
league = League(league_id=LEAGUE_ID, year=2021, espn_s2=ESPN_S2, swid=SWID)

# print(league.standings())

# print(league.power_rankings(week = 1))


@app_2.route('/')
def home():
    teams = sorted(league.teams, key=lambda x: x.standing)
    matchups = league.scoreboard()
    return render_template('index.html', teams=teams, matchups=matchups)


@app_2.route('/headtohead')
def head_to_head():
    seasons = range(2021, 2024)  # Adjust based on how long your league has existed
    head_to_head_records = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # wins, losses

    all_team_names = set()

    for year in seasons:
        try:
            season_league = League(
                league_id=LEAGUE_ID,
                year=year,
                espn_s2=ESPN_S2,
                swid=SWID
            )
        except Exception as e:
            print(f"Could not load league for {year}: {e}")
            continue

        for week in range(1, 18):  # max 17 weeks in regular season
            try:
                scoreboard = season_league.scoreboard(week)
            except:
                continue

            for matchup in scoreboard:
                if not matchup.home_team or not matchup.away_team:
                    continue

                home = matchup.home_team.team_name
                away = matchup.away_team.team_name
                home_score = matchup.home_score
                away_score = matchup.away_score

                all_team_names.update([home, away])

                if home_score > away_score:
                    head_to_head_records[home][away][0] += 1  # home win
                    head_to_head_records[away][home][1] += 1  # away loss
                elif away_score > home_score:
                    head_to_head_records[away][home][0] += 1  # away win
                    head_to_head_records[home][away][1] += 1  # home loss
                # ties not counted

    teams = sorted(all_team_names)
    table = []

    for team in teams:
        row = {'team': team, 'record': {}}
        for opponent in teams:
            if opponent == team:
                row['record'][opponent] = '—'
            else:
                wins, losses = head_to_head_records[team][opponent]
                row['record'][opponent] = f'{wins}-{losses}'
        table.append(row)

    return render_template('headtohead.html', table=table, teams=teams)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app_2.run(debug=True, host='0.0.0.0', port=port)