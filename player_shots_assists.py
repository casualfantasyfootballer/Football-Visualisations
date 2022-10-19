#program starts on line 503. Up to line 500 are functions that are used within the program. 


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
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm
from highlight_text import ax_text,fig_text

#####################################################################################################################
#these values are changed each time that the program is run
single_players_understat = [7752] #add more than one understat ID to create shot/assisted shot maps for more than 1 player
date_6_gw_ago = datetime.datetime(2022,8,30) #alter this to the GW that is 6 GWS ago from the current GW
today = '19-10-22' #the date that the visualisation is created
season = 2022 #used in understat calls
gameweek = 12 #used to calculate the below values
prev_count = gameweek-6
next_count = gameweek

#####################################################################################################################

#font that is used through the viz
fm_rubik = FontManager(('https://github.com/google/fonts/blob/main/ofl/bebasneue/'
                        'BebasNeue-Regular.ttf?raw=true'))
#understat calls
#returns a json file containing all of the shots that a given player has taken this season
async def gt_player_shots(player_id):
    async with aiohttp.ClientSession() as session: 
        understat = Understat(session)
        player_shots = await understat.get_player_shots(player_id, {'season':str(season)}) 
    return json.dumps(player_shots)

#returns a json file containing all of the shots for other players where the focus player has been credited with the assist
async def gt_assisted_player_shots(player_id,focused_player):
    async with aiohttp.ClientSession() as session: 
        understat = Understat(session)
        player_shots = await understat.get_player_shots(player_id, {'season':'2022','player_assisted':focused_player}) 
    return json.dumps(player_shots)

#required to go thorugh all other player for the same team as the focused player
async def get_team_mates(team_name):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        results = await understat.get_team_players(
            team_name,
            season,
        )
    return json.dumps(results)

#reduces the need to check if EVERY player in the squad has had a shot. Small amount of time saved. 
async def player_with_no_shots(player_id):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        grouped_stats = await understat.get_player_grouped_stats(player_id)
        return json.dumps(grouped_stats)

#######################################################################################################################

#retrievs ONLY that data that is required later
async def retrieve_player_shots(p_id):
    json_data = await gt_player_shots(p_id)
    json_data = json.loads(json_data)
    p_shts = list(json_data)

    if len(p_shts) > 0:
        player_name = json_data[0]['player']
        if p_shts[-1]['h_a'] == 'h': #-1 takes into account the latest team player has played for this season. This helps if a player transfers midway through a season. 
            player_team = p_shts[-1]['h_team']
        else:
            player_team = p_shts[-1]['a_team']

        p_shts_v2 = []
        for i in range(len(p_shts)):
            for j in range(len(pl_teams)):
                if p_shts[i]['h_team'] == pl_teams[j]['title']:
                    p_shts_v2.append(p_shts[i])

        #from the player ID, you can get the player name, the team they play for and their shot data
        return [player_name,player_team,p_shts_v2]

async def retrieve_team_mates(t_id):
    json_data = await get_team_mates(t_id)
    json_data = json.loads(json_data)
    t_mates = list(json_data)

    return t_mates #returns a list of the team mates for our focus player

async def retrieve_assisted_shots(team_mate_list,focused_player_id):
    assissted_shots = []

    for i in range(len(team_mate_list)):
        player_id = team_mate_list[i]['id']
        json_data = await gt_assisted_player_shots(player_id,focused_player_id)
        json_data = json.loads(json_data)
        assissted_shts = list(json_data)
        
        for j in range(len(assissted_shts)):
            assissted_shots.append(assissted_shts[j])

    return assissted_shots

#whole function to determine which data belowng in the last 6 GW's. This serves as a focus 
def previous_6_gws(p_shts, assissted_shots):
    prev_six_gw_date = date_6_gw_ago

    prev_6_gw_shots = []
    prev_6_gw_assisted_shots = []

    player_shots = []
    player_assisted_shots = []

    player_goals = []
    assisted_goals = []

    prev_6_player_goals = []
    prev_6_assisted_goals = []

    for i in range(len(p_shts)):
        p_shts[i]['X'] = float(p_shts[i]['X'])*100
        p_shts[i]['Y'] = float(p_shts[i]['Y'])*100
        format_date = datetime.datetime.strptime(str(p_shts[i]['date']), '%Y-%m-%d %H:%M:%S')
        if p_shts[i]['result'] == 'Goal':
            if format_date >= prev_six_gw_date:
                prev_6_player_goals.append(p_shts[i])
            else:
                player_goals.append(p_shts[i])
        else:
            if format_date >= prev_six_gw_date:
                prev_6_gw_shots.append(p_shts[i])
            else:
                player_shots.append(p_shts[i])
        
    for i in range(len(assissted_shots)):
        assissted_shots[i]['X'] = float(assissted_shots[i]['X'])*100
        assissted_shots[i]['Y'] = float(assissted_shots[i]['Y'])*100
        format_date = datetime.datetime.strptime(str(assissted_shots[i]['date']), '%Y-%m-%d %H:%M:%S')
        if assissted_shots[i]['result'] == 'Goal':
            if format_date >= prev_six_gw_date:
                prev_6_assisted_goals.append(assissted_shots[i])
            else:
                assisted_goals.append(assissted_shots[i])
        else:
            if format_date >= prev_six_gw_date:
                prev_6_gw_assisted_shots.append(assissted_shots[i])
            else:
                player_assisted_shots.append(assissted_shots[i])

    return([prev_6_gw_shots,
    prev_6_gw_assisted_shots,
    player_shots,
    player_assisted_shots,
    player_goals,
    assisted_goals,
    prev_6_player_goals,
    prev_6_assisted_goals])

###########################################################################################################################
#needed to check for transfers in since start of season. Keep shot data for pl to pl team transfers but not outside of pl
#only need to run once to find 20 teams as all players should look for the same 20 teams
#would waste processing time doing this again & again
async def all_pl_teams():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        results = await understat.get_teams(
            "epl",
            2022
        )
    return json.dumps(results)

teams_json_data = asyncio.run(all_pl_teams())
teams_json_data = json.loads(teams_json_data)
pl_teams = list(teams_json_data)
      

#functions for plotting shots###############################################################################################

def make_a_plot(dataframe,main_colour,hatching,edges,symbol,legend_text,where_to_plot):
    pitch.scatter(dataframe.X, dataframe.Y,
            s=(dataframe.xG * 5400) + 600,
            c=main_colour,
            hatch = hatching,
            edgecolors = edges,
            marker = symbol,
            label = legend_text,
            ax=where_to_plot)

def make_a_plot_6_weeks(dataframe,main_colour,edges,symbol,legend_text,where_to_plot):
    pitch.scatter(dataframe.X, dataframe.Y,
            s=(dataframe.xG * 5400) + 600,
            c=main_colour,
            edgecolors = edges,
            marker = symbol,
            label = legend_text,
            ax=where_to_plot)

def make_a_plot_player_2(dataframe,main_colour,hatching,edges,symbol,where_to_plot):
    pitch.scatter(dataframe.X, dataframe.Y,
            s=(dataframe.xG * 5400) + 600,
            c=main_colour,
            hatch = hatching,
            edgecolors = edges,
            marker = symbol,
            ax=where_to_plot)

def make_a_plot_6_weeks_player_2(dataframe,main_colour,edges,symbol,where_to_plot):
    pitch.scatter(dataframe.X, dataframe.Y,
            s=(dataframe.xG * 5400) + 600,
            c=main_colour,
            edgecolors = edges,
            marker = symbol,
            ax=where_to_plot)

#shot & assists stats#################################################################################################
#data is imported from a pickle file to reduce the number of calls made to understat. 
#I found i could run this program once to create a file and then use the file as many times as needed. 
#as the season progressess, it could take up to 20 minutes to produce the file. You do not want to spend 20 minutes per player creating a chart. 
df = pd.read_pickle("D:\\$ Personal\\FPL\\13). Player Shots & Assist Maps\\player_shot_data.pkl")
stats_list = df.values.tolist()

def ranking(player_id):

    season_shots = 0
    last_6_shots = 0
    season_xg = 0
    last_6_xg = 0
    season_assists = 0
    last_6_assists = 0
    season_xa = 0
    last_6_xa = 0

    #sort for shots rank
    shots_rank = sorted(stats_list,key = itemgetter(3), reverse = True)
    s_rank = 0
    for i in range(len(shots_rank)):
        if int(shots_rank[i][0]) == player_id:
            s_rank = i+1
            season_shots = shots_rank[i][3]
            last_6_shots = shots_rank[i][6]
            season_xg = round(shots_rank[i][2],3)
            last_6_xg = round(shots_rank[i][7],3)
            season_assists = shots_rank[i][4]
            last_6_assists = shots_rank[i][8]
            season_xa = round(shots_rank[i][5],3)
            last_6_xa = round(shots_rank[i][9],3)

    #sort for last_6 shot rank
    l6_shot_rank = sorted(stats_list,key = itemgetter(6), reverse = True)
    l6s_rank = 0
    for i in range(len(l6_shot_rank)):
        if int(l6_shot_rank[i][0]) == player_id:
            l6s_rank = i+1

    l6s_rank_colour = ''
    if l6s_rank < s_rank:
        l6s_rank_colour = '#4EFF83'
    elif l6s_rank > s_rank:
        l6s_rank_colour ='#FF055B'
    else:
        l6s_rank_colour ='#AFB0B3'

    #sort season xg rank
    shot_xg_rank = sorted(stats_list,key = itemgetter(2), reverse = True)
    xg_rank = 0
    for i in range(len(shot_xg_rank)):
        if int(shot_xg_rank[i][0]) == player_id:
            xg_rank = i+1

    #sort last 6 xg rank
    l6_shot_xg_rank = sorted(stats_list,key = itemgetter(7), reverse = True)
    l6_xg_rank = 0
    for i in range(len(l6_shot_xg_rank)):
        if int(l6_shot_xg_rank[i][0]) == player_id:
            l6_xg_rank = i+1

    l6s_xg_rank_colour = ''
    if l6_xg_rank < xg_rank:
        l6s_xg_rank_colour = '#4EFF83'
    elif l6_xg_rank > xg_rank:
        l6s_xg_rank_colour ='#FF055B'
    else:
        l6s_xg_rank_colour ='#AFB0B3'

    #sort season assist rank
    sa_rank = sorted(stats_list,key = itemgetter(4), reverse = True)
    a_rank = 0
    for i in range(len(sa_rank)):
        if int(sa_rank[i][0]) == player_id:
            a_rank = i+1

    #sort assists in last 6 weeks rank
    l6_sa_rank = sorted(stats_list,key = itemgetter(8), reverse = True)
    l6_a_rank = 0
    for i in range(len(l6_sa_rank)):
        if int(l6_sa_rank[i][0]) == player_id:
            l6_a_rank = i+1

    l6s_sa_rank_colour = ''
    if l6_a_rank < a_rank:
        l6s_sa_rank_colour = '#4EFF83'
    elif l6_a_rank > a_rank:
        l6s_sa_rank_colour ='#FF055B'
    else:
        l6s_sa_rank_colour ='#AFB0B3'

    #sort season xa
    season_xa_rank = sorted(stats_list,key = itemgetter(5), reverse = True)
    xa_rank = 0
    for i in range(len(season_xa_rank)):
        if int(season_xa_rank[i][0]) == player_id:
            xa_rank = i+1

    #sort last 6 gw xa rank
    last6_xa_rank = sorted(stats_list,key = itemgetter(9), reverse = True)
    l6_xa_rank = 0
    for i in range(len(last6_xa_rank)):
        if int(last6_xa_rank[i][0]) == player_id:
            l6_xa_rank = i+1

    l6s_xa_rank_colour = ''
    if l6_xa_rank < xa_rank:
        l6s_xa_rank_colour = '#4EFF83'
    elif l6_xa_rank > xa_rank:
        l6s_xa_rank_colour ='#FF055B'
    else:
        l6s_xa_rank_colour ='#AFB0B3'
    
    return([season_shots, last_6_shots, season_xg, last_6_xg, season_assists, last_6_assists, season_xa, last_6_xa,
    s_rank, l6s_rank, xg_rank, l6_xg_rank, a_rank, l6_a_rank, xa_rank, l6_xa_rank,
    l6s_rank_colour, l6s_xg_rank_colour, l6s_sa_rank_colour, l6s_xa_rank_colour])

#get FPL ID for those selected from understat#################################################################################

async def off_fpl_players():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        player = await fpl.get_players(return_json=True)
    return player

async def all_teams_info():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        teams = await fpl.get_teams(return_json=True)
    return teams

fpl_players = asyncio.run(off_fpl_players())
fpl_players_list = list(fpl_players)
fpl_teams = asyncio.run(all_teams_info())

def find_fpl_data(all_fpl_players, all_fpl_teams, name_to_convert, team_to_check):

    #understat & fpl have different names for teams
    if team_to_check == "Manchester City":
        team_to_check = "Man City"
    elif team_to_check == "Manchester United":
        team_to_check = "Man Utd"
    elif team_to_check == "Newcastle United":
        team_to_check = "Newcastle"
    elif team_to_check == "Tottenham":
        team_to_check = "Spurs"
    elif team_to_check == "Wolverhampton Wanderers":
        team_to_check = "Wolves"
    elif team_to_check == "Nottingham Forest":
        team_to_check = "Nott'm Forest"

    for i in range(len(all_fpl_players)):
        name_to_check = name_to_convert.split()
        fpl_name = all_fpl_players[i]['web_name'].split()
        fpl_surname = fpl_name[-1].split('.')
        fpl_first_name = fpl_name[0]
        fpl_official_surname = all_fpl_players[i]['second_name']

        if unidecode.unidecode(fpl_surname[-1].lower()) == unidecode.unidecode(name_to_check[-1].lower()):           
            if all_fpl_teams[int(all_fpl_players[i]["team"]-1)]["name"].lower() == team_to_check.lower():
                player_photo = all_fpl_players[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                fpl_team_id = all_fpl_players[i]['team']

        elif unidecode.unidecode(fpl_first_name.lower()) == unidecode.unidecode(name_to_check[-1].lower()):
            if fpl_teams[int(fpl_players_list[i]["team"]-1)]["name"].lower() == team_to_check.lower():
                player_photo = all_fpl_players[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                fpl_team_id = all_fpl_players[i]['team']

        elif unidecode.unidecode(fpl_first_name.lower()) == unidecode.unidecode(name_to_check[0].lower()):
            if fpl_teams[int(fpl_players_list[i]["team"]-1)]["name"].lower() == team_to_check.lower():
                player_photo = all_fpl_players[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                fpl_team_id = all_fpl_players[i]['team']

        elif unidecode.unidecode(fpl_official_surname.lower()) == unidecode.unidecode(name_to_check[-1].lower()):
            if fpl_teams[int(all_fpl_players[i]["team"]-1)]["name"].lower() == team_to_check.lower():
                player_photo = all_fpl_players[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                fpl_team_id = all_fpl_players[i]['team']
        
        elif len(name_to_check) > 1:
            if unidecode.unidecode(fpl_first_name.lower()) == unidecode.unidecode(name_to_check[1].lower()):
                if fpl_teams[int(fpl_players_list[i]["team"]-1)]["name"].lower() == team_to_check.lower():
                    player_photo = all_fpl_players[i]['photo'].split('.')
                    player_photo_string = player_photo[0]
                    fpl_team_id = all_fpl_players[i]['team']
        
        if all_fpl_players[i]["web_name"].lower() == "smith rowe" and name_to_check == "emile smith-rowe": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']

        #special name cases as their names are presented with/without special characters on the two sites
        if all_fpl_players[i]["web_name"].lower() == "smith rowe" and unidecode.unidecode(name_to_convert.lower()) == "emile smith-rowe": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']
        
        if all_fpl_players[i]["web_name"].lower() == "aït-nouri" and unidecode.unidecode(name_to_convert.lower()) == "rayan ait nouri": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']

        if all_fpl_players[i]["web_name"].lower() == "de cordova-reid" and unidecode.unidecode(name_to_convert.lower()) == "bobby reid": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']

        if all_fpl_players[i]["web_name"].lower() == "bella-kotchap" and unidecode.unidecode(name_to_convert.lower()) == "armel bella kotchap": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']
        
        if all_fpl_players[i]["web_name"].lower() == "o'brien" and name_to_convert.lower() == "lewis o&#039;brien": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']

        #konsa (villa) uses middle name - this could be improved in future iterations
        if all_fpl_players[i]["web_name"].lower() == "konsa" and unidecode.unidecode(name_to_convert.lower()) == "ezri konsa ngoyo": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']
        #also uses middle name
        if all_fpl_players[i]["web_name"].lower() == "bech" and unidecode.unidecode(name_to_convert.lower()) == "mads bech sorensen": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']
        #also uses middle name
        if all_fpl_players[i]["web_name"].lower() == "sambi" and unidecode.unidecode(name_to_convert.lower()) == "albert sambi lokonga": 
            player_photo = all_fpl_players[i]['photo'].split('.')
            player_photo_string = player_photo[0]
            fpl_team_id = all_fpl_players[i]['team']

    #need to also return team id - for prev 6 & next 6 GW's
    return ([player_photo_string, fpl_team_id])

#FDR Calcs###################################################################################################################

async def fpl_fixtures(gw):
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        fix = await fpl.get_fixtures_by_gameweek(gw,return_json=True)
    return fix

async def all_teams():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        fix = await fpl.get_teams(return_json=True)
    return fix

def fdr_calculator(counter, team_id):
    all_t = asyncio.run(all_teams())
    fixtures = []
    for i in range(6):
        gw_fixtures = asyncio.run(fpl_fixtures(counter))
        fixt = []
        for j in range(len(gw_fixtures)):
            if gw_fixtures[j]['team_a'] == team_id :
                fixt.append(gw_fixtures[j]['team_h']) 
                fixt.append(gw_fixtures[j]['team_a_difficulty'])
                for k in range(len(all_t)):
                    if all_t[k]['id'] == gw_fixtures[j]['team_h']:
                        fixt.append(all_t[k]['short_name'])
                fixt.append("(A)")
            elif gw_fixtures[j]['team_h'] == team_id:    
                fixt.append(gw_fixtures[j]['team_a']) 
                fixt.append(gw_fixtures[j]['team_h_difficulty'])
                for k in range(len(all_t)):
                    if all_t[k]['id'] == gw_fixtures[j]['team_a']:
                        fixt.append(all_t[k]['short_name'])
                fixt.append("(H)")
        fixtures.append(fixt)
        counter += 1
    return fixtures

#PROGRAM STARTS############################################################################################

for i in range(len(single_players_understat)):
    returned_player_details = asyncio.run(retrieve_player_shots(single_players_understat[i]))
    if returned_player_details is not None:
        name = returned_player_details[0]
        team = returned_player_details[1]
        shots = returned_player_details[2]
    else:
        name = 'Jamie Vardy'
        team = 'Leicester'
        shots = []

    #create a function to get FPL related data
    fpl_player_data = find_fpl_data(fpl_players_list, fpl_teams, name, team)
    player_photo = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+str(fpl_player_data[0])+'.png'
    fpl_team = fpl_player_data[1]

    #fixtuers lists
    prev = fdr_calculator(prev_count, fpl_team)
    next_f = fdr_calculator(next_count, fpl_team) 

    teams_text = []
    colours = []

    for j in range(len(prev)):
        t_txt = ''
        if len(prev[j]) > 4:
            t_txt = prev[j][2]+prev[j][3]+'\n'+prev[j][6]+prev[j][7]
            colours.append('#E7E7E7')
        elif len(prev[j]) > 0:
            t_txt = prev[j][2]+'\n'+prev[j][3]
            if prev[j][1] == 5:
                colours.append('#80072D')
            elif prev[j][1] == 4:
                colours.append('#FF1751')
            elif prev[j][1] == 3:
                colours.append('#E7E7E7')
            elif prev[j][1] == 2:
                colours.append('#02FC79')
            elif prev[j][1] == 1:
                colours.append('#375523')
        else:
            colours.append('#E7E7E7')
        teams_text.append(t_txt)

    upcoming_teams_text = []
    upcoming_colours = []

    for j in range(len(next_f)):
        t_txt = ''
        if len(next_f[j]) > 4:
            t_txt = next_f[j][2]+next_f[j][3]+'\n'+next_f[j][6]+next_f[j][7]
            upcoming_colours.append('#E7E7E7')
        elif len(next_f[j]) > 0:
            t_txt = next_f[j][2]+'\n'+next_f[j][3]
            if next_f[j][1] == 5:
                upcoming_colours.append('#80072D')
            elif next_f[j][1] == 4:
                upcoming_colours.append('#FF1751')
            elif next_f[j][1] == 3:
                upcoming_colours.append('#E7E7E7')
            elif next_f[j][1] == 2:
                upcoming_colours.append('#02FC79')
            elif next_f[j][1] == 1:
                upcoming_colours.append('#375523')
        else:
            upcoming_colours.append('#E7E7E7')
        upcoming_teams_text.append(t_txt)


    team_mates = asyncio.run(retrieve_team_mates(team)) 
    assists = asyncio.run(retrieve_assisted_shots(team_mates,name))

    data = previous_6_gws(shots,assists)

    ranks = ranking(single_players_understat[i])

    player_shots_df = pd.DataFrame.from_dict(data[2])
    assissted_shots_df = pd.DataFrame.from_dict(data[3])
    prev_player_shots_df = pd.DataFrame.from_dict(data[0])
    prev_assissted_shots_df = pd.DataFrame.from_dict(data[1])
    player_goals_df = pd.DataFrame.from_dict(data[4])
    assisted_goals_df = pd.DataFrame.from_dict(data[5])
    prev_player_goals_df = pd.DataFrame.from_dict(data[6])
    prev_assisted_goals_df = pd.DataFrame.from_dict(data[7])

    if len(player_shots_df) > 0:
        player_shots_df['xG'] = pd.to_numeric(player_shots_df['xG'])

    if len(assissted_shots_df) > 0:
        assissted_shots_df['xG'] = pd.to_numeric(assissted_shots_df['xG'])

    if len(prev_player_shots_df) > 0:    
        prev_player_shots_df['xG'] = pd.to_numeric(prev_player_shots_df['xG'])

    if len(prev_assissted_shots_df) > 0:    
        prev_assissted_shots_df['xG'] = pd.to_numeric(prev_assissted_shots_df['xG'])

    if len(player_goals_df) > 0:
        player_goals_df['xG'] = pd.to_numeric(player_goals_df['xG'])

    if len(assisted_goals_df) > 0:    
        assisted_goals_df['xG'] = pd.to_numeric(assisted_goals_df['xG'])

    if len(prev_player_goals_df) > 0:    
        prev_player_goals_df['xG'] = pd.to_numeric(prev_player_goals_df['xG'])

    if len(prev_assisted_goals_df) > 0:    
        prev_assisted_goals_df['xG'] = pd.to_numeric(prev_assisted_goals_df['xG'])


    pitch = VerticalPitch(pad_bottom=0.5,
            half=True,
            goal_type='box',
            goal_alpha=0.8,
            pitch_color = "#1A1A1A",
            pitch_type='opta')
    fig, ax = pitch.draw(figsize=(24, 20))

    ax.set_ylim(40, 102)

    if len(player_goals_df) > 0:
        make_a_plot(player_goals_df,'None','///','#4EFF83','X','Player Goals - Whole Season',ax)   

    if len(assisted_goals_df) > 0:
        make_a_plot(assisted_goals_df,'None','///','#05F1FF','X','Player Assists - Whole Season',ax)

    if len(player_shots_df) > 0:
        make_a_plot(player_shots_df,'None','///','#EBFF01','o','Player Shots - Whole Season',ax)

    if len(assissted_shots_df) > 0:
        make_a_plot(assissted_shots_df,'None','///','#FF055B','o','Player Assisted Shots - Whole Season',ax)

    if len(prev_assissted_shots_df) > 0:
        make_a_plot_6_weeks(prev_assissted_shots_df,'#FF055B','#37003C','o','Player Assisted Shots - Prev 6 GW',ax)

    if len(prev_player_shots_df) > 0:   
        make_a_plot_6_weeks(prev_player_shots_df,'#EBFF01','#FF055B','o','Player Shots - Prev 6 GW',ax)                 

    if len(prev_assisted_goals_df) > 0:
        make_a_plot_6_weeks(prev_assisted_goals_df,'#05F1FF','#37003C','X','Player Assisted Goals - Prev 6 GW',ax)  
        
    if len(prev_player_goals_df) > 0:
        make_a_plot_6_weeks(prev_player_goals_df,'#4EFF83','#37003C','X','Player Goals - Prev 6 GW',ax)  

    txt = ax.text(x=100, y=108, s=name,
            size=150,
            fontproperties=fm_rubik.prop, color=pitch.line_color,
            va='center', ha='left')

    ax_text(100, 103.5, '<Goals> <Assists> <Shots> <Assisted Shots>',
        fontsize=40,
        va='center',
        ha='left',
        color = pitch.line_color,
        weight='bold',
        fontproperties=fm_rubik.prop,
        highlight_textprops=[{"color": '#4EFF83'},{"color": '#05F1FF'},{"color": '#EBFF01'},{"color": '#FF055B'}])

    ax.add_patch(patches.Rectangle((94, 101), 6,1, facecolor = '#1A1A1A' , edgecolor = '#4EFF83', hatch = '///'))
    ax_text(93.5, 101.5, ' = Data from games not witihin the last 6 GW\'s', fontsize = 25, color = pitch.line_color, va = 'center', ha = 'left', fontproperties=fm_rubik.prop,)


    #stats table
    s_txt = ax.text(x = 66, y = 60, s="Shots" ,size = 40, color=pitch.line_color, va='center', ha='left', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 66, y = 57, s="Rank" ,size = 40, color=pitch.line_color, va='center', ha='left', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 66, y = 54, s="Assists" ,size = 40, color=pitch.line_color, va='center', ha='left', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 66, y = 51, s="Rank" ,size = 40, color=pitch.line_color, va='center', ha='left', fontproperties=fm_rubik.prop)

    ax.text(x=54,y=63.5, s="Season\nCount",size = 40, color=pitch.line_color,va='center', ha='center', fontproperties=fm_rubik.prop)
    ax.text(x=42,y=63.5, s="Last 6GW\nCount",size = 40, color=pitch.line_color,va='center', ha='center', fontproperties=fm_rubik.prop)
    ax.text(x=30,y=63.5, s="Season xG\nPer Shot",size = 40, color=pitch.line_color,va='center', ha='center', fontproperties=fm_rubik.prop)
    ax.text(x=18,y=63.5, s="Last 6GW xG\nPer Shot",size = 40, color=pitch.line_color,va='center', ha='center', fontproperties=fm_rubik.prop)

    s_txt = ax.text(x = 54, y = 60, s=str(ranks[0]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 42, y = 60, s=str(ranks[1]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 30, y = 60, s=str(ranks[2]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 18, y = 60, s=str(ranks[3]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)

    s_txt = ax.text(x = 54, y = 57, s=str(ranks[8]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 42, y = 57, s=str(ranks[9]) ,size = 40, color=ranks[16], va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 30, y = 57, s=str(ranks[10]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 18, y = 57, s=str(ranks[11]) ,size = 40, color=ranks[17], va='center', ha='center', fontproperties=fm_rubik.prop)

    s_txt = ax.text(x = 54, y = 54, s=str(ranks[4]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 42, y = 54, s=str(ranks[5]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 30, y = 54, s=str(ranks[6]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 18, y = 54, s=str(ranks[7]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)

    s_txt = ax.text(x = 54, y = 51, s=str(ranks[12]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 42, y = 51, s=str(ranks[13]) ,size = 40, color=ranks[18], va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 30, y = 51, s=str(ranks[14]) ,size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    s_txt = ax.text(x = 18, y = 51, s=str(ranks[15]) ,size = 40, color=ranks[19], va='center', ha='center', fontproperties=fm_rubik.prop)

    ax.plot([66, 11], [61.5, 61.5], lw='1', c=pitch.line_color)
    ax.plot([66, 11], [58.5, 58.5], lw='1', c=pitch.line_color)
    ax.plot([66, 11], [55.5, 55.5], lw='1', c=pitch.line_color)
    ax.plot([66, 11], [52.5, 52.5], lw='1', c=pitch.line_color)

    data = [[95,90,85,80,75,70],[47,45,47,45,47,45]]
    next_data = [[30,25,20,15,10,5],[45,47,45,47,45,47]]

    for i in range(len(teams_text)):
        ax.plot(data[0][i],data[1][i],marker="H", color=colours[i], ms=85)
    
    texts = [ax.text(data[0][i], data[1][i], teams_text[i], color = "#1A1A1A", size = 28, va='center', ha='center', fontproperties=fm_rubik.prop) for i in range(len(teams_text))] 

    for i in range(len(upcoming_teams_text)):
        ax.plot(next_data[0][i],next_data[1][i],marker="H", color=upcoming_colours[i], ms=85)
    
    texts = [ax.text(next_data[0][i], next_data[1][i], upcoming_teams_text[i], color = "#1A1A1A", size = 28, va='center', ha='center', fontproperties=fm_rubik.prop) for i in range(len(teams_text))] 

    ax.text(x=82.5, y=42, s="Previous 6 Fixtures", size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    ax.text(x=17.5, y=42, s="Upcoming 6 Fixtures", size = 40, color=pitch.line_color, va='center', ha='center', fontproperties=fm_rubik.prop)
    
    fig.set_facecolor("#1A1A1A")#FPLOTD
    #fig.set_facecolor("#131722")


    fig.text(0.545,0.85,'Made by Andrew Brown | @casualfantasypl | Data from Understat', size=25, color = "#ADAEB1", fontproperties=fm_rubik.prop)
    #plt.show()

    #left, bottom, width, height .... 0.2, 0.425
    ax_player = fig.add_axes([0.13,0.095,0.2,0.425])
    ax_player.axis('off')
    im = plt.imread(player_photo)
    ax_player.imshow(im)

    plt.savefig('D:\\$ Personal\\FPL\\13). Player Shots & Assist Maps\\' + name + ' ' + today + ' Shots & Assists.png', bbox_inches = 'tight')




############################################################################################################################

