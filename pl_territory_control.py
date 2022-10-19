import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from matplotlib import rcParams, colors
from mplsoccer import Pitch, VerticalPitch, FontManager
from highlight_text import ax_text,fig_text
import matplotlib.image as mpimg
import asyncio
import aiohttp
from mplsoccer.utils import FontManager
from highlight_text import ax_text,fig_text
from fpl import FPL
import unidecode

#required to run asynchronous functions
import nest_asyncio
nest_asyncio.apply()

with open('D:\\$ Personal\\FPL\\whoscored.json', "r") as json_file:
    ws_data = json.load(json_file)

players = ws_data['playerIdNameDictionary']
h_team = ws_data['home']['teamId']
a_team = ws_data['away']['teamId']
h_team_name = ws_data['home']['name']
a_team_name = ws_data['away']['name']
highlight_h_team_name = '<' + h_team_name + '>'
highlight_a_team_name = '<' + a_team_name + '>'
score = ws_data['score']
h_score = score[0]
a_score = score[-1]

async def all_players():
  async with aiohttp.ClientSession() as session:
    fpl = FPL(session)
    players = await fpl.get_players(return_json=True)   
    return players

async def all_teams():
  async with aiohttp.ClientSession() as session:
    fpl = FPL(session)
    teams = await fpl.get_teams(return_json=True)   
    return teams

player_result = asyncio.run(all_players())
teams_result = asyncio.run(all_teams())

#team name check function
def team_name_convert(team_to_check):
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
  return team_to_check

h_fpl_team_id = 0
a_fpl_team_id = 0

for i in range(len(teams_result)):
  if str(teams_result[i]['name']) == team_name_convert(h_team_name):
    h_fpl_team_id = teams_result[i]['id']
  elif str(teams_result[i]['name']) == team_name_convert(a_team_name):
    a_fpl_team_id = teams_result[i]['id']

player_images = []
for i in players:
  player_images.append("")
match_count = 0

player_result = list(player_result)
for i in range(len(player_result)):

    if player_result[i]['team'] == h_fpl_team_id or player_result[i]['team'] == a_fpl_team_id:
        matched = 0
        for player in players:
            fpl_name = player_result[i]['web_name'].split()
            fpl_surname = fpl_name[-1].split(".")
            fpl_first_name = fpl_name[0]
            name_to_check = players[player].split()
            fpl_official_surname = player_result[i]['second_name']

            if unidecode.unidecode(fpl_surname[-1].lower()) == unidecode.unidecode(name_to_check[-1].lower()) and 'reece' == unidecode.unidecode(name_to_check[0].lower()):
                player_index = list(players).index(player)
                player_photo = player_result[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                player_images[player_index] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+player_photo_string+'.png'
                match_count+=1
            
            elif unidecode.unidecode(fpl_surname[-1].lower()) == unidecode.unidecode(name_to_check[-1].lower()):    
                #print("FPL: " + player_result[i]['web_name'] + " MATCHED " + players[player])
                player_index = list(players).index(player)
                player_photo = player_result[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                player_images[player_index] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+player_photo_string+'.png'
                match_count+=1

            elif unidecode.unidecode(fpl_first_name.lower()) == unidecode.unidecode(name_to_check[-1].lower()):
                matched = 1
                #print("FPL: " + player_result[i]['web_name'] + " MATCHED " + players[player])
                player_index = list(players).index(player)
                player_photo = player_result[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                player_images[player_index] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+player_photo_string+'.png'
                match_count+=1

            elif unidecode.unidecode(fpl_first_name.lower()) == unidecode.unidecode(name_to_check[0].lower()):
                matched = 1
                #print("FPL: " + player_result[i]['web_name'] + " MATCHED " + players[player])
                player_index = list(players).index(player)
                player_photo = player_result[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                player_images[player_index] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+player_photo_string+'.png'
                match_count+=1

            elif unidecode.unidecode(fpl_official_surname.lower()) == unidecode.unidecode(name_to_check[-1].lower()):
                matched = 1
                #print("FPL: " + player_result[i]['web_name'] + " MATCHED " + players[player])
                player_index = list(players).index(player)
                player_photo = player_result[i]['photo'].split('.')
                player_photo_string = player_photo[0]
                player_images[player_index] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+player_photo_string+'.png'
                match_count+=1

            elif len(name_to_check) > 1:
                if unidecode.unidecode(fpl_official_surname.lower()) == unidecode.unidecode(name_to_check[1].lower()):
                    matched = 1
                    #print("FPL: " + player_result[i]['web_name'] + " MATCHED " + players[player])
                    player_index = list(players).index(player)
                    player_photo = player_result[i]['photo'].split('.')
                    player_photo_string = player_photo[0]
                    player_images[player_index] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'+player_photo_string+'.png'
                    match_count+=1

#there were 2 x James's in Chel V Leeds. I therfore just manually overwrote one of them. 
player_images[-7] = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p225796.png'


h_touches = []
a_touches = []

for event in ws_data['events']:
  if event['isTouch'] == True:
    if event['teamId'] == h_team:
      h_touches.append(event)
    else:
      a_touches.append(event)

#playertouches - similar to home & away touches
player_touches = []
for i in players:
  player_touches.append([])

for event in ws_data['events']:
  if event['isTouch'] == True:
    for player in players:
      try:
        if int(event['playerId']) == int(player):
          player_index = list(players).index(player)
          player_touches[player_index].append(event)
      except:
        pass

count = 0
for player in players:
  #print(players[player] + ": " + str(len(player_touches[list(players).index(player)])))
  count+=1

h_touches_x_y = [[],[]]
for i in range(len(h_touches)):
    h_touches_x_y[0].append(float(h_touches[i]['x']))
    h_touches_x_y[1].append(float(h_touches[i]['y']))
    
a_touches_x_y = [[],[]]
for i in range(len(a_touches)):
    a_touches_x_y[0].append(100 - float(a_touches[i]['x']))
    a_touches_x_y[1].append(100 - float(a_touches[i]['y']))

player_x_y_touches = []

for i in range(len(player_touches)):
  x_y = [[],[]]
  for j in range(len(player_touches[i])):
    if player_touches[i][j]['teamId'] == a_team:
      x_y[0].append(100 - float(player_touches[i][j]['x']))
      x_y[1].append(100 - float(player_touches[i][j]['y']))
    else:
      x_y[0].append(float(player_touches[i][j]['x']))
      x_y[1].append(float(player_touches[i][j]['y']))
  player_x_y_touches.append(x_y)

league_logo = mpimg.imread('D:\\$ Personal\\FPL\\$ Logos\\prem_logo_edited.png')

fm_rubik = FontManager(('https://github.com/google/fonts/blob/main/ofl/bebasneue/'
                        'BebasNeue-Regular.ttf?raw=true'))
text_colour = '#989898'
cmap = colors.ListedColormap(['#FF005A','#05F1FF','#ffc505']) #custom color map normal = ['#35cada','#da4535','#f27127']
pitch = Pitch(pitch_type='opta',  pad_top = 10, line_zorder=2, line_color='#FFFFFF', pitch_color='#1A1A1A')
fig, axs = pitch.draw(figsize=(15,12))
fig.set_facecolor('#1A1A1A')
bins = (6,4)

home_touch_zones = pitch.bin_statistic(h_touches_x_y[0],h_touches_x_y[1], statistic ='count', bins = bins)
away_touch_zones = pitch.bin_statistic(a_touches_x_y[0],a_touches_x_y[1], statistic ='count', bins = bins)

#alters the statistics so the colour is solid & not gradient
for j in range(len(home_touch_zones['statistic'])):
        for k in range(len(home_touch_zones['statistic'][j])):
            total_touches = home_touch_zones['statistic'][j][k] + away_touch_zones['statistic'][j][k]
            if home_touch_zones['statistic'][j][k] < (total_touches * 0.55) and home_touch_zones['statistic'][j][k] > (total_touches * 0.45):
                home_touch_zones['statistic'][j][k] = 100
            elif home_touch_zones['statistic'][j][k] > away_touch_zones['statistic'][j][k]:
                home_touch_zones['statistic'][j][k] = 50
            else:
                home_touch_zones['statistic'][j][k] = 0
hm = pitch.heatmap(home_touch_zones, ax=axs, cmap=cmap, edgecolors = '#131722')

player_touch_zones = []
for i in range(len(player_x_y_touches)):
  player_touch_zones.append(pitch.bin_statistic(player_x_y_touches[i][0], player_x_y_touches[i][1], statistic ='count', bins = bins))

players_list = list(players)

highest_values = []
player_ids = []
player_names = []
for i in range(4):
  to_add = []
  to_add2 = []
  to_add_3 = []
  for i in range(6):
    to_add.append(0)
    to_add2.append(0)
    to_add_3.append("")
  highest_values.append(to_add)
  player_ids.append(to_add2)
  player_names.append(to_add_3)

for player in range(len(player_touch_zones)):
  for i in range(len(player_touch_zones[player]['statistic'])):
    for j in range(len(player_touch_zones[player]['statistic'][i])):
      #print(player_touch_zones[0]['statistic'][i][j])
      if player_touch_zones[player]['statistic'][i][j] > highest_values[i][j]:
        highest_values[i][j] = player_touch_zones[player]['statistic'][i][j]
        p_id = players_list[player]
        name = players[p_id].split() #= names
        player_names[i][j] = name[-1]
        player_ids[i][j] = player_images[player]
      elif player_touch_zones[player]['statistic'][i][j] == highest_values[i][j]:
        player_ids[i][j] = "Players of same touches"
        player_names[i][j] = ">1 Player\nwith Highest\nNo of Touches"

#player_touches[list(players).index(player)
#rearrange these so the plot from bottom to top, not top to bottom. 
x_pos = 0.04
x_pos_add = 0.155
y_pos = 0.1095 
y_pos_add = 0.1885
img_count = 0

img_list = []
for i in range(24):
  img_list.append([])

img_row = 0
img_col = 0

for i in range(len(img_list)):
  img_count += 1
  img_list[i] = fig.add_axes([x_pos,y_pos, 0.075, 0.1])
  img_list[i].axis('off')
  print(player_ids[img_row][img_col])
  if player_ids[img_row][img_col] != "Players of same touches":
    if player_ids[img_row][img_col] != "No Image Found":
      print(player_ids[img_row][img_col])
      im = plt.imread(player_ids[img_row][img_col])
      img_list[i].imshow(im)
  img_col += 1
  x_pos += x_pos_add
  if img_count % 6 == 0:
    y_pos += y_pos_add
    x_pos = 0.04
    img_row += 1
    img_col = 0

name_height = 0.225
name_col = 0.05
name_count = 0
name_row = 0
name_column = 0

for i in range(24):
  name_count += 1
  fig.text(x=name_col, y=name_height, s=player_names[name_row][name_column],
              fontproperties=fm_rubik.prop, 
          fontsize=20,
          color='#1A1A1A',
              va='center', ha='left')
  name_col += 0.155
  name_column += 1
  if name_count % 6 == 0:
    name_height += 0.188
    name_col = 0.05
    name_row += 1
    name_column = 0

ax_league_logo = fig.add_axes([0.825,0.9,0.175,0.175])
ax_league_logo.axis('off')
ax_league_logo.imshow(league_logo)

fig.text(x=0.03, y=1.06, s='Who Controlled Where in the match',
            fontproperties=fm_rubik.prop, 
         fontsize=60,
         color=text_colour,
            va='center', ha='left')

fig.text(x=0.03, y=1, s=h_team_name + ": " + h_score,
            fontproperties=fm_rubik.prop, 
         fontsize=60,
         color='#05F1FF',
            va='center', ha='left')

fig.text(x=0.03, y=0.94, s=a_team_name + ": " + a_score,
            fontproperties=fm_rubik.prop, 
         fontsize=60,
         color='#FF005A',
            va='center', ha='left')

fig_text(x=0.03, y=0.89, fontsize=30, s='<Contested Zones> Where no team has more than 55% of total touches',
          va='center',
          ha='left',
          color = text_colour,
          weight='bold',
          fontproperties=fm_rubik.prop,
          highlight_textprops=[{"color": '#ffc505'}],
        ax=axs)



fig.text(0.6755 ,0.07,'Made by Andrew Brown | @casualfantasypl | Data from Opta', fontproperties=fm_rubik.prop, fontsize=15, color = "#ADAEB1")
fig.text(0.628,0.05,'Heavily inspired by @johnspacemuller, @Odriozolite & @petermckeever', fontproperties=fm_rubik.prop, fontsize=15, color = "#ADAEB1")

plt.savefig("D:\\$ Personal\\FPL\\15) Single Game Territory\\PL_Territory.jpg", facecolor = '#1A1A1A', bbox_inches='tight')