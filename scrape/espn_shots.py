"""
Scrape ESPN.com for shot chart information

TO DO: 
    - I think this is a subset of all play-by-play information. How to get all of it?

"""
import re as re
import requests as requests
import sys as sys
import sqlite3
from random import random
from time import sleep, gmtime, strftime
from bs4 import BeautifulSoup

import espn_master

ESPN_NBA_SHOT_URL = 'http://sports.espn.go.com/nba/gamepackage/data/shot?gameId='
ESPN_NBA_SHOT_COLS = ['shot_id','game_id','pid','p','t','gtime','qtr','res','dist_ft','shot_type','x','y']
ESPN_GAME_IDS = {'2010-2011': (301026002, 310413030),
                 '2011-2012': (311225006, 320426030),
                 '2012-2013': (400277721, 400440940)}
SLEEP_SEC = 2 # Average number of seconds to sleep between hitting of web page

def scrape_shots(espn_game_id):
    '''
    Components of the shot:
    id 	    --> composed of id_espn_game + 0 + [play-by-play ID]
    pid     --> player ID    
    qtr     --> quarter (what does OT look like??)
    x       --> x-cord where shot was taken from
    y       --> y-cord where shot was taken from    
    t       --> values: a(way), h(ome)
    made    --> true/false
    p       --> player name
    d       --> description e.g. "Made 19ft jumper 11:44 in 1st Qtr"
	
    Source: http://www.basketballgeek.com/data/    
    How do I interpret the (x,y) shot location coordinates?:
    If you are standing behind the offensive team's hoop then
    the X axis runs from left to right and the Y axis runs from
    bottom to top. The center of the hoop is located at (25, 5.25).
    x=25 y=-2 and x=25 y=96 are free-throws (8ft jumpers)
    '''
    page = requests.get('%s%s' % (ESPN_NBA_SHOT_URL, espn_game_id))
    xml = BeautifulSoup(page.text)
    return map(lambda x: x.attrs, xml.findAll('shot'))

def parse_description(description):
    """
    Parse the shot descriptions e.g. Made 1ft jumper 11:40 in 1st Qtr
    """	
    pattern = re.compile('(\w+) (\d+)ft ([\w\d\-]+) ([\d\:]+) in (\d)\w+ (\w+)')
    m = re.match(pattern, description)
    if m is not None:
	return dict(zip([u'res',u'dist_ft',u'shot_type',u'gtime',u'per',u'per_type'], m.groups()))
    else:
	return dict()

def update_table(db, game_ids):
    """
    Update the ESPN_NBA_SHOT table
    """
    for game_id in game_ids:
        shots = scrape_shots(game_id)
        shots2 = list()
        for shot in shots:
            # Clean up identifiers and parse description
            shot[u'game_id'] = game_id
            shot[u'shot_id'] = shot['id']
            shot = dict(shot, **parse_description(shot['d']))
            shots2.append([shot[key] for key in ESPN_NBA_SHOT_COLS]) # TO DO: Link this to schema.sql        
        db.executemany('INSERT INTO ESPN_NBA_SHOT VALUES ('+','.join(['?']*len(ESPN_NBA_SHOT_COLS))+')', shots2)
        print 'Inserted gameId=%s into ESPN_NBA_SHOT at %s!' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
        sleep(random()*SLEEP_SEC)        
        db.commit()
        
def clean_table(db):
    """
    Clean the raw ESPN_NBA_SHOT table based on quirks I have noticed from analysis
    """
    # These appear to be free-throws from cross-referencing with PBP
    db.execute('delete from espn_nba_shot where (y=-2 or y=96) and x=25')
    # Top/bottom code based on court dimensions (94 ft by 50 ft)
    db.execute('update espn_nba_shot set x = 0 where x<0')
    db.execute('update espn_nba_shot set x = 50 where x>50')
    db.execute('update espn_nba_shot set y = 0 where y<0')
    db.execute('update espn_nba_shot set y = 50 where y>94')
    # Remove free throws     
    db.commit()

if __name__=='__main__':
    """
    For running from terminal...
    Usage: python espn_shots.py "[date]" "[db_path]"
    """	
    date, db_path = sys.argv[1:3] # The path is currently "../core-data.db"
    db = sqlite3.connect('db_path') # TO DO: Store DB_PATH in a CONFIG file    
    game_ids = espn_master.scrape_game_ids(date) # TO DO: Set this up to run every day
    update_table(db, game_ids)
    clean_table(db)
    db.close()
    
    # TO DO: Add logging capabilities
    
