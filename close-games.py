
# Get NBA team IDs
from nba_api.stats.static import teams
nba_teams = teams.get_teams()
nba_team_ids = [team["id"] for team in nba_teams]

from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.library.parameters import SeasonTypeAllStar
# Game finder for season and season type
gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable = "2020-21",
    season_type_nullable = SeasonTypeAllStar.playoffs, timeout = 10)

# Extract game IDs
games_dict = gamefinder.get_normalized_dict()
games = games_dict["LeagueGameFinderResults"]
game_ids = [game["GAME_ID"] for game in games if game["TEAM_ID"] in nba_team_ids] # filter to nba teams only

# Print game IDs
print(len(game_ids))

from nba_api.stats.endpoints import playbyplay
import pandas as pd
import time

def timeConvert(mins, secs):
    return (60 * mins + secs)

def getIntByGameID(game_id):
    time.sleep(0.5)
    df = playbyplay.PlayByPlay(game_id).get_data_frames()[0]

    # Select rows with scores
    df = df.loc[df["SCORE"].notnull()]

    # Clean up columns
    df[["minute", "second"]] = df["PCTIMESTRING"].str.split(":", expand = True).astype(int)
    df[["left_score", "right_score"]] = df["SCORE"].str.split(" - ", expand = True).astype(int)
    df.rename(columns = {"PERIOD":"period"}, inplace = True)
    df = df.loc[:, ["period", "minute", "second", "left_score", "right_score"]]

    df.to_excel("heat-bucks1.xlsx")

    #Loop through all scores
    totTime = 0
    integral = 0

    #Keep track of the previous row to calculate difference
    pMins = 12
    pSecs = 0
    pLeft = 0
    pRight = 0
    for row in df.itertuples():
        dt = abs(timeConvert(pMins, pSecs) - timeConvert(row.minute, row.second))

        if dt == 720 or (row.period >= 5 and dt == 300):
            print("New quarter shit")
            dt = 0

        totTime += dt
        integral += dt * abs(pLeft - pRight)

        pMins = row.minute
        pSecs = row.second
        pLeft = row.left_score
        pRight = row.right_score

    print("Completed game" + game_id)
    print("GIntegral: " + str(integral))
    print("Total time: " + str(totTime))
    print("Point difference per second: " + str(float(integral/(totTime))))
    print()


    return float(integral/totTime)


output_dict = {}
pointspersec = []

for i in game_ids:
    pointspersec.append(getIntByGameID(i))

output_dict = dict(zip(game_ids, pointspersec))

keys = output_dict.keys()
values = output_dict.values()

df2 = pd.DataFrame({"GameID": keys, "PD": values})
df2.to_excel("playoffPD.xlsx")
