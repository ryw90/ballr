"""
Master functions for interacting with ESPN
"""
from time import sleep
from random import random
import datetime as dt
import requests as requests
import re as re
import sys
import sqlite3
import dataset # TO DO: Get rid of this dependency

import espn_shots

"""
Constants
TO DO: Move these to a CONFIG file
"""
ESPN_NBA_SCOREBOARD_URL = 'http://sports.espn.go.com/nba/scoreboard?date='
SLEEP_SEC = 2 # Average number of seconds to sleep between hitting of web page
NBA_SEASONS = {'2007-2008': ( dt.date(2007,10,30), dt.date(2008,4,16) ), # [year] : ([start], [end])
               '2008-2009': ( dt.date(2008,10,28), dt.date(2009,4,16) ),
               '2009-2010': ( dt.date(2009,10,27), dt.date(2010,4,14) ),
               '2010-2011': ( dt.date(2010,10,26), dt.date(2011,4,13) ),
               '2011-2012': ( dt.date(2011,12,25), dt.date(2012,4,26) ), # shortened season
               '2012-2013': ( dt.date(2012,10,30), dt.date(2013,4,17) )}
               
DB_PATH = '../core_data.db'
SCHEMA_PATH = '../schema/core_data.sql'               

def scrape_game_ids(date_id):
    """
    Input:
	date_id - of the form (YYYYMMDD)
    Output:
	A list of game IDs
    """  
    if isinstance(date_id, list):
        def pause_sgi(date_id):
            print 'pausing'
            sleep(random()*SLEEP_SEC)
            return scrape_game_ids(date_id)
        return [gid for dt in date_id for gid in pause_sgi(dt)]
    elif isinstance(date_id, str):
        page = requests.get('%s%s' % (ESPN_NBA_SCOREBOARD_URL,date_id))
        game_pattern = re.compile('var thisGame = new gameObj\("(\d{7,12})".*\)')
        return game_pattern.findall(page.text)
    else:
        raise Exception('Cannot deal with that type of date_id')
        
def init_db():
    """
    Initialize the db
    """
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, mode='r') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    conn.close()        
        
if __name__=='__main__':
    """
    TO DO: Write in usage, check if we have game_ids
    """
    args = sys.argv[1:]    
    db = dataset.connect('sqlite:///%s') % DB_PATH
            
    # Load a whole season's worth of data
    if args[0] == 'season':
        season = args[1]
        start, end = NBA_SEASONS[season]
        dates = [start + dt.timedelta(x) for x in range((end-start).days+1)]
        date_ids = [str(date).replace('-','') for date in dates]
        game_ids = scrape_game_ids(date_ids)
        espn_shots.update_table(db, game_ids)    
        
    # Load a whole day's worth of data
    if args[0] == 'date':
        pass # TO DO:
        
    # Load data for days in a date-range
    if args[0] == 'date-range':
        pass # TO DO:
    
    # Load data for a set of game_ids
    if args[0] == 'game_ids':
        pass # TO DO:

                