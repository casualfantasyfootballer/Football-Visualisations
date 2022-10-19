import asyncio
import json
import aiohttp
from understat import Understat
from fpl import FPL
import matplotlib.pyplot as plt
import datetime
from operator import itemgetter
import unidecode
from mplsoccer import VerticalPitch, Pitch
from mplsoccer.utils import FontManager
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm

season = 2022
date_6_gw_ago = datetime.datetime(2022,8,30) # year, month, day

#get all the players in the EPL who have played more than 600

async def all_understat_players():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        players = await understat.get_league_players(
            "epl",
            2022,
        )
        return json.dumps(players)

players = asyncio.run(all_understat_players())
players = json.loads(players)
players = list(players)

#print(players[0])

################################################################################################################

player_xg_data = []

for i in range(len(players)):
    data = []
    if players[i]['position'] != 'GK' and int(players[i]['shots']) >= 1:
        data.append(players[i]['id'])
        data.append(players[i]['player_name'])
        data.append(float(players[i]['npxG'])/int(players[i]['shots']))
        data.append(int(players[i]['shots']))
        player_xg_data.append(data)

print(player_xg_data[0])

################################################################################################################

async def gt_player_shots(player_id):
    async with aiohttp.ClientSession() as session: 
        understat = Understat(session)
        player_shots = await understat.get_player_shots(player_id, {'season':str(season)}) 
    return json.dumps(player_shots)



#gather all the shots. manually find out who assisted each shot to save on time consuming requests. 
all_player_shots = []

for i in range(len(player_xg_data)):
    just_player_shots = asyncio.run(gt_player_shots(player_xg_data[i][0])) #7230 = ESR/Arsenal
    just_player_shots = json.loads(just_player_shots)
    just_player_shots = list(just_player_shots)
    all_player_shots.append(just_player_shots)

#print(len(all_player_shots))
#print(all_player_shots[0][0])

########################################################################################################################################

for player in range(len(player_xg_data)):
    assists = 0
    xA = 0
    last_6_shots = 0
    last_6_xg = 0
    last_6_assisted = 0
    last_6_xa = 0
    for p_shots in range(len(all_player_shots)):
        for shots in range(len(all_player_shots[p_shots])):
            format_date = datetime.datetime.strptime(str(all_player_shots[p_shots][shots]['date']), '%Y-%m-%d %H:%M:%S')
            if all_player_shots[p_shots][shots]['player_id'] == player_xg_data[player][0] and all_player_shots[p_shots][shots]['situation'] != 'Penalty':
                if format_date > date_6_gw_ago:
                    last_6_shots += 1
                    last_6_xg = last_6_xg + float(all_player_shots[p_shots][shots]['xG']) 

            if all_player_shots[p_shots][shots]['situation'] != 'Penalty':
                if all_player_shots[p_shots][shots]['player_assisted'] == player_xg_data[player][1]:
                    assists += 1
                    xA = xA + float(all_player_shots[p_shots][shots]['xG'])
                    if format_date > date_6_gw_ago:
                        last_6_assisted += 1
                        last_6_xa = last_6_xa + float(all_player_shots[p_shots][shots]['xG'])

    if assists > 0:
        xG_per_assist = float(xA/assists)
    else:
        xG_per_assist = 0

    if last_6_shots > 0:
        last_6_xg_per_shot = float(last_6_xg/last_6_shots)
    else:
        last_6_xg_per_shot = 0

    if last_6_assisted > 0:
        last_6_xa_per_shot = float(last_6_xa/last_6_assisted)
    else:
        last_6_xa_per_shot = 0
    

    player_xg_data[player].append(assists)
    player_xg_data[player].append(xG_per_assist)
    player_xg_data[player].append(last_6_shots)
    player_xg_data[player].append(last_6_xg_per_shot)
    player_xg_data[player].append(last_6_assisted)
    player_xg_data[player].append(last_6_xa_per_shot)

print(player_xg_data[0])

df = pd.DataFrame(player_xg_data, columns = ['id', 'name', 'xg_ps', 'shots', 'assists', 'xg_pa', 'l6_shots', 'l6_xgps', 'l6_assists', 'l6_xg_pa'])
df.to_pickle("D:\\$ Personal\\FPL\\13). Player Shots & Assist Maps\\player_shot_data.pkl")
