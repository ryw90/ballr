import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import numpy as np

db = sqlite3.connect('core_data.db')
shots = db.cursor().execute('select * from espn_nba_shot where game_id < 400488874').fetchall()
headers = [x[1] for x in db.cursor().execute('pragma table_info(espn_nba_shot)').fetchall()]
shots = pd.DataFrame(shots, columns=headers)

shots[['x','y','dist_ft']] = shots[['x','y','dist_ft']].astype(int)
shots['made'] = (shots.res=='Made').astype(int)

shots = shots[shots.x >= 0] # cull shots ( TO DO: Think about how to do this without messing up points scored and such...)
shots = shots[shots.x < 51]
shots = shots[shots.y >= 0]
shots = shots[shots.y < 96]
shots = shots[shots.dist_ft < 35] # too long

shots['y2'] = shots.y # flip home shots so that we just have one basket
shots.y2[shots.t=="h"] = 97 - shots.y[shots.t=='h']

shots['x_3by3'] = ceil(shots.x/3.)*3-1.5
shots['y_3by3'] = ceil(shots.y2/3.)*3-1.5

# Calculate FG%
# Decide whether or not to bin further
plyr_shot_loc = shots.groupby(['pid','p','x','y'])['made'].sum() 

## TEST 'HEAT MAP' WITH RAY ALLEN
import scipy.interpolate

tmp = shots[shots.p=="Stephen  Curry"]
tmp_grp = tmp.groupby(['x_3by3','y_3by3'])
shot_count = tmp_grp.size() # Number of shots
shot_count2 = shot_count / float(sum(shot_count)) # Proportion of shots
fg_pct = tmp_grp['made'].mean()

x, y = zip(*shot_count.index)
x = np.array(x)
y = np.array(y)
z = np.array(shot_count2)

# cm = plt.cm.get_cmap('RdYlBu') # colors
# plt.scatter(map(lambda x: x*3-1.5, x), map(lambda y: y*3-1.5,y), c=1-fg_pct, cmap=cm, s=shot_count2*50/mean(shot_count2))
# plt.scatter(x, y, c=1-fg_pct, cmap=cm, s=shot_count*50)
# plt.scatter(x, y, c=shot_count, cmap=cm)
# colorbar()

# Try some kind of interpolation

res = 500
xi, yi = np.linspace(x.min(), x.max(), res), np.linspace(y.min(), y.max(), res)
xi, yi = np.meshgrid(xi, yi)

rbf = scipy.interpolate.Rbf(x, y, z, function='linear')
zi = rbf(xi, yi)

fig = plt.figure()
plt.imshow(zi, extent=[x.min(), x.max(), y.min(), y.max()], origin='lower', vmin=z.min(), vmax=z.max(), cmap=plt.cm.get_cmap('Reds'))

# 3 Point Line
plt.plot([47, 47], [0, 14], 'k-')
plt.plot([3, 3], [0, 14], 'k-')
axes().add_patch(matplotlib.patches.Arc(xy=(25,14), width=44, height=31, angle=0, theta1=0, theta2=180))

# threes = shots[shots.shot_type=="3-pointer"][['x','y2']].drop_duplicates()
# plt.scatter(threes.x, threes.y2)

# Free throw lane
plt.plot([31, 31], [0, 19], 'k-')
plt.plot([19, 19], [0, 19], 'k-')
plt.plot([19, 31], [19, 19], 'k-')
axes().add_patch(plt.Circle(xy=(25,19), radius=6, fill=False))

#for X, Y, Z in zip(x, y, z):
#    plt.annotate('{}'.format(Z), xy=(X,Y))