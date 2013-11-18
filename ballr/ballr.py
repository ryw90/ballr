# -*- coding: utf-8 -*-
"""
    Ballr
    ~~~~~~

    A bare-bones Flask application using Flask and sqlite3 (based on the example flaskr application)

    by Ryan Wang (2013)
    
    TO DO:
        - Fix a bug involving player ids = '0984' vs '984' (Tyson Chandler)
"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import pandas as pd
import numpy as np
import ballr_utilities 


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='C:/Users/r_wang/Desktop/ballr/data/core_data.db', # 'data/core_data.db'
    DEBUG=True,
    SECRET_KEY='development key',
    FIRST_GAME_2013=400488874
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
        
    
@app.route('/')
def show_players():
    db = get_db()
    cur = db.execute('select distinct p, pid from espn_nba_shot where cast(game_id as integer)>=%d' % app.config['FIRST_GAME_2013'])
    players = cur.fetchall()
    return render_template('show_players.html', players=players)

        
@app.route('/shot_chart/<pid>')
def shot_chart(pid):
    db = get_db()
    cur = db.execute('select cast(x as int), cast(y as int), res from espn_nba_shot where pid=%s' % pid)
    shots = cur.fetchall()
    
    # Plot made/missed shots
    miss, made = reduce(lambda x,y: x[y[2]=='Made'].append(y) or x, shots, ([],[]))    
    miss_x, miss_y, _ = zip(*miss)
    made_x, made_y, _ = zip(*made)
    return ballr_utilities.shot_chart_matplotlib(made_x, made_y, miss_x, miss_y)
    
@app.route('/shot_freq_map/<pid>')
def shot_freq_map(pid):            
    db = get_db()
    cur = db.execute('select cast(x as int), cast(y as int), t from espn_nba_shot where pid=%s' % pid)
    shots = pd.DataFrame(map(list, cur.fetchall()), columns=['x','y','t'])
    
    # Clean the shots data
    shots = shots[shots.x >= 0] # Outside of normal dimensions
    shots = shots[shots.x < 51]
    shots = shots[shots.y >= 0]
    shots = shots[shots.y < 97]
    shots.y[shots.t=="h"] = 97 - shots.y[shots.t=="h"] # Put home and away shots on same side
    
    # Calculate shot frequency on an aggregated grid
    shots['x_3by3'] = np.ceil(shots.x/3.)*3-1.5
    shots['y_3by3'] = np.ceil(shots.y/3.)*3-1.5
    shot_count = shots.groupby(['x_3by3','y_3by3']).size()
    shot_prop = shot_count / float(sum(shot_count))
    shot_x, shot_y = zip(*shot_prop.index)
    
    return ballr_utilities.shot_freq_map_matplotlib(shot_x, shot_y, shot_count, label=True)
    

if __name__ == '__main__':    
    app.run()