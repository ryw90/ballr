"""
Scrape ESPN.com for shot chart information

NOTE: I think this is a subset of all play-by-play information. How to get all of it?

RW (11/13/2013)

"""
import dataset as dataset
import re as re
import requests as requests
import sys as sys
from random import random
from time import sleep, gmtime, strftime
from bs4 import BeautifulSoup

ESPN_NBA_SHOT_URL = 'http://sports.espn.go.com/nba/gamepackage/data/shot'
SLEEP_SECS = 2 # Average number of seconds to sleep between hitting of web page

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
    page = requests.get('%s?gameId=%s' % (ESPN_NBA_SHOT_URL, espn_game_id))
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
        for shot in shots:
            shot.update(parse_description(shot['d']))
            shot[u'game_id'] = game_id
            shot[u'shot_id'] = shot['id']
            del shot['id'] # Don't allow the shot dict to have a field called 'id'
            db['ESPN_NBA_SHOT'].insert(shot)
        print 'Inserted gameId=%s into ESPN_NBA_SHOT at %s!' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
        sleep(random()*SLEEP_SECS)

if __name__=='__main__':
    """
    For running from terminal...
    Usage: python espn_shots.py "[date]" "[db_path]"
    """	
    #date, db_path = sys.argv[1:3] # The path is currently "../bball.db"
    #db = dataset.connect('sqlite:///%s' % db_path) # TO DO: Store the db_location in a CONFIG file
    #print db.tables
    #game_ids = scrape_game_ids(date) # TO DO: Set this up to run every day
    #update_table(db, game_ids)
    
    # TO DO: Add logging capabilities
        

    

