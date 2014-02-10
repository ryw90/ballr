# -*- coding: utf-8 -*-
"""
    Ballr
    ~~~~~~

    A bare-bones Flask application using Flask and sqlite3
    
"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from math import log     
import pandas as pd
import numpy as np
import ballr_util, os

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='c:/users/rywang/documents/github/ballr/db/core_data.db', # 'data/core_data.db'
    DEBUG=True,
    SECRET_KEY='development key'    
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# Database
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

# Pages     
@app.route('/')
def about():
    return render_template('about.html')
    
@app.route('/stats')
def stats():    
    db = get_db()
    stats = dict()
    for s in ['pts','ast','reb','blk','stl','tos']:
        cur = db.execute('select player, %s from espn_nba_per_game \
                            order by %s desc limit 10' % (s,s))
        stats[s] = cur.fetchall()
    print len(stats)
    return render_template('stats.html', stats=stats)    

@app.route('/charts')
def charts():
    db = get_db()
    cur = db.execute('select player, gp, pid from espn_nba_per_game')
    players = cur.fetchall()   
    return render_template('charts.html', players=players)

@app.route('/heat_map/<pid>')
def heat_map(pid):
    db = get_db()
    cur = db.execute('select * from espn_nba_shot_agg where pid=?', (pid,))
    shots = pd.DataFrame(map(list, cur.fetchall()), columns=['pid','p','x','y','shot_freq'])    
    img = {'base64': ballr_util.heat_map_rbf(shots.x, shots.y, np.log(shots.shot_freq))}
    return render_template('heat_map.html', img=img, pname=shots.p[0])

if __name__ == '__main__':    
    app.run()
    