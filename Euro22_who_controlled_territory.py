from statsbombpy import sb
import pandas as pd
import matplotlib.pyplot as plt
from operator import itemgetter
from adjustText import adjust_text
from highlight_text import ax_text,fig_text
from mplsoccer import Pitch
from matplotlib import colors

#Get all matches for Euro 2022
comp = sb.competitions()
matches = sb.matches(competition_id = 55, season_id = 43)
#convert DataFrame to Dictionary. I prefer working values in a Dict instead of a DF
matches_dict = matches.to_dict(orient='records') 
sorted_matches = sorted(matches_dict, key=itemgetter('match_date'))

#Create a list of all teams competing at Euro 2022
column_values = matches[['home_team']].values.ravel()
teams = pd.unique(column_values)
teams.sort()

###Collect all touch data######################################################
#initiate a list to keep a track of all touches made in the tournament
#1st dimension of the list represents teams
#2nd dimension of the list makes the team the 'home team' & all opponents the 'away team'
#3rd dimnension holds the X & Y values of each touch.
tournament_touches = []

for team in range(len(teams)):
    
    team_name = teams[team]
    home_touches = []
    away_touches = []

    for match in range(len(sorted_matches)):
        if sorted_matches[match]['home_team'] == team_name \
            or sorted_matches[match]['away_team'] == team_name:
            match = sb.events(match_id=sorted_matches[match]['match_id']) 
            match_dict = match.to_dict('records')

            for touch in range(len(match_dict)):
                if match_dict[touch]['possession_team'] == team_name:
                    #try and except is used to deal with Nan values
                    try:
                        if pd.isna(match_dict[touch]['location']) == False:
                            home_touches.append(match_dict[touch]['location'])
                    except:
                        home_touches.append(match_dict[touch]['location'])
                else:
                    try:
                        if pd.isna(match_dict[touch]['location']) == False:
                            away_touches.append(match_dict[touch]['location'])
                    except:
                        away_touches.append(match_dict[touch]['location'])
                        
    #statsbomb automatically record data as teams playing from left to right
    #this swaps values so that the away team pays right to left. 
    for i in range(len(away_touches)):
        away_touches[i][0] = 120 - away_touches[i][0]
        away_touches[i][1] = 80 - away_touches[i][1]
                        
    tournament_touches.append([home_touches,away_touches])

###specifically sort the X & Y values so they can be plotted onto the pich#####
tournament_x_y_touches = []

for i in range(len(tournament_touches)):
    
    home_x_y_touches = [[],[]]
    for j in range(len(tournament_touches[i][0])):
        home_x_y_touches[0].append(tournament_touches[i][0][j][0])
        home_x_y_touches[1].append(tournament_touches[i][0][j][1])

    away_x_y_touches = [[],[]]
    for j in range(len(tournament_touches[i][1])):
        away_x_y_touches[0].append(tournament_touches[i][1][j][0])
        away_x_y_touches[1].append(tournament_touches[i][1][j][1])
        
    tournament_x_y_touches.append([home_x_y_touches,away_x_y_touches])


#using only 3 colours forces the heatmpa function to plot solif colours rather than a traditional heatmap sliding scale
cmap = colors.ListedColormap(['#CCCCCC','#9656A2','#B02C3F']) #custom color map.
pitch = Pitch(pitch_type='statsbomb',
                pad_top = 10,
                line_zorder=2,
                line_color='#FFFFFF',
                pitch_color='#131722')
fig, axs = pitch.grid(nrows=6,
                        ncols=4,
                        grid_width=0.88,
                        left=0.025,
                        figheight=30,
                        endnote_height=0.06,
                        endnote_space=0,
                        axis=False,
                        title_space=0.02,
                        title_height=0.06,
                        grid_height=0.8)
bins = (6, 4)

for i,ax in enumerate(axs['pitch'].flat):

    #Values for the bins need to be generated to do a comparison to see which team controls the terratory for that bin. 
    home_touch_zones = pitch.bin_statistic(tournament_x_y_touches[i][0][0],
            tournament_x_y_touches[i][0][1],
            statistic='count',
            bins=bins)
    away_touch_zones = pitch.bin_statistic(tournament_x_y_touches[i][1][0],
            tournament_x_y_touches[i][1][1],
            statistic='count',
            bins=bins)
    
    #Iterate over each bin and reassign their values. 
    #100 represent home team territory
    #50 represents contested territory
    #0 represents away team territory
    for j in range(len(home_touch_zones['statistic'])):
        for k in range(len(home_touch_zones['statistic'][j])):
            total_touches = home_touch_zones['statistic'][j][k] + away_touch_zones['statistic'][j][k]
            if home_touch_zones['statistic'][j][k] < (total_touches * 0.55) and home_touch_zones['statistic'][j][k] > (total_touches * 0.45):
                home_touch_zones['statistic'][j][k] = 100
            elif home_touch_zones['statistic'][j][k] > away_touch_zones['statistic'][j][k]:
                home_touch_zones['statistic'][j][k] = 50
            else:
                home_touch_zones['statistic'][j][k] = 0

    #plot the heatmap        
    hm = pitch.heatmap(home_touch_zones, ax=ax, cmap=cmap, edgecolors = '#131722')
    #title for each plot on the grid
    ax_text(0, -10, teams[i], ha='left', va='center', fontsize=30, ax=ax, color = "#ADAEB1")

fig.set_facecolor("#131722")

#Graphic text
axs['title'].text(0.475,
                    0.65,
                    'Who Controlled Territory? Euro 2020',
                    fontsize=40,
                    va='center',
                    ha='right',
                    color = "#ADAEB1")
SUB_TEXT = 'Posession by zone in Euro 2020'
axs['title'].text(0.3615,
                    0.35,
                    SUB_TEXT,
                    fontsize=35,
                    va='center',
                    ha='right',
                    color = "#ADAEB1")
ax_text(0.6125,
        14.75,
        '<Team>, Opponent, <Contested> Less Than 55% & More Than 45%',
        fontsize=30,
        va='center',
        ha='right',
        color = "#ADAEB1",
        highlight_textprops=[{"color": '#9656A2'},{"color": '#B02C3F'}])
axs['endnote'].text(0.65,
                    0.09,
                    'Made by PUT NAME HERE. Data from StatsBomb.',
                    size=16,
                    color = "#ADAEB1")

plt.savefig("PUT NAME OF FILE HERE.jpg", bbox_inches = 'tight')
