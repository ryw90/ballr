"""
Scrape ESPN.com for various information (shot location, box score, pbp)

TO DO:
    - Add logging capabilities
    - Add backup capabilities
    - Move data cleaning code
"""

import datetime as dt
import re
import requests

from bs4 import BeautifulSoup
from random import random
from time import sleep, gmtime, strftime


"""
Global variables esp. crucial URLs from ESPN.com
"""
ESPN_NBA_SCOREBOARD_URL = 'http://sports.espn.go.com/nba/scoreboard?date='
ESPN_NBA_BOX_URL = 'http://sports.espn.go.com/nba/boxscore?gameId='
ESPN_NBA_PBP_URL = 'http://sports.espn.go.com/nba/playbyplay?gameId='
ESPN_NBA_SHOT_URL = 'http://sports.espn.go.com/nba/gamepackage/data/shot?gameId='

NBA_SEASONS = {'2007-2008': ( dt.date(2007,10,30), dt.date(2008,4,16) ),
               '2008-2009': ( dt.date(2008,10,28), dt.date(2009,4,16) ),
               '2009-2010': ( dt.date(2009,10,27), dt.date(2010,4,14) ),
               '2010-2011': ( dt.date(2010,10,26), dt.date(2011,4,13) ),
               '2011-2012': ( dt.date(2011,12,25), dt.date(2012,4,26) ), # shortened season
               '2012-2013': ( dt.date(2012,10,30), dt.date(2013,4,17) )}

SLEEP_SEC = 1 # Average no. of seconds to sleep between requests


"""
Game IDs
"""
def scrape_game_ids(date_id):
    """
    Scrape ESPN's game_ids from daily scoreboards
    Input:
		date_id - of the form (YYYYMMDD)
    Output:
		A list of game IDs
    """  
    if isinstance(date_id, list):
    	# Allow for pausing when scraping multiple dates
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


"""
Box score data
"""
def scrape_box_ov(game_id):
	"""
	Scrape game overview from box score page e.g. date, teams, attendance	
	"""
	url = '%s%s' % (ESPN_NBA_BOX_URL, game_id)
	page = requests.get(url)
	if page.url == url: # In case of redirect
		soup = BeautifulSoup(page.text)
		box_ov = list()		        
        # Teams and scores
        try:
            line_score = soup.find('table', attrs={'class':'linescore'})
            _, away_team, home_team = map(lambda x: x.text, line_score.findAll('td', attrs={'class':'team'})) # Teams
            away_score, home_score = map(lambda x: x.text, line_score.findAll('td', attrs={'class':'ts'})) # Scores
            box_ov.extend([away_team, away_score, home_team, home_score])
        except:
            box_ov.extend([None, None, None, None])        
        # Pre-game details
        game_vitals = soup.find('div', attrs={'class':'game-vitals'})
        coverage, date_time, arena = map(lambda x: x.text, game_vitals.findAll('p'))
        tmp = date_time.split(',')
        game_time_et = tmp[0].strip()
        game_date = ','.join(tmp[1:]).strip()
        box_ov.extend([game_time_et, game_date, arena, coverage])
        # Post-game details
        try:
            tmp = list()
            for key in ['Officials', 'Attendance', 'Time of Game']:
                m = re.search(r'%s:\s*</strong>\s*([\w\,\:\s]+)\s*<br>' % key, page.text)
                if m is not None:
                    tmp.append(m.group(1))
                else:
                    tmp.append(None)
            box_ov.extend(tmp)
            box_ov[9] = box_ov[9].replace(',','') # Scrub attendance
        except:
            box_ov.extend([None, None, None])       
        return box_ov


def scrape_box(game_id):
    """
    Scrape player stats from box score e.g. points, rebounds, etc.
    """    
    url = '%s%s' % (ESPN_NBA_BOX_URL, game_id)        
    page = requests.get(url)
    if page.url == url:
        soup = BeautifulSoup(page.text)
        box_lines = soup.findAll('tr', class_=re.compile(r'player'))
        box = list()
        for line in box_lines:
            pid = line.find('a')['href'].split('/')[7] # Heavily hard-coded
            stats = [s.text for s in line.findAll('td')]
            if stats != []:
                plyr, pos = [s.strip() for s in stats[0].split(',')]
                if 'DNP' in stats[1]:
                    box.append([pid, plyr, pos] + [None]*14)
                else:
                    box.append([pid, plyr,pos] + stats[1:])
        return box


def update_box_ov(db, game_ids):
    """
    Update the ESPN_NBA_BOX_OV table
    """
    box_ov = list()
    for game_id in game_ids:
        box_ov.append([game_id] + scrape_box_ov(game_id))
        print 'JUST SCRAPED BOX FOR %s at %s' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
        sleep(random()*SLEEP_SEC)
    db.executemany('INSERT INTO ESPN_NBA_BOX_OV VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', box_ov)
    db.commit()
    print 'INSERTED %d RECORDS INTO ESPN_NBA_BOX_OV' % len(box_ov)


def update_box(db, game_ids):    
    """
    Update the ESPN_NBA_BOX table
    """
    box = list()
    for game_id in game_ids:
        box.extend(map(lambda l: [game_id] + l, scrape_box(game_id)))
        print 'JUST SCRAPED BOX FOR %s at %s' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))        
        sleep(random()*SLEEP_SEC)
    db.executemany('INSERT INTO ESPN_NBA_BOX VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', box)
    db.commit()
    print 'INSERTED %d RECORDS INTO ESPN_NBA_BOX' % len(box)    


"""
Play-by-play
"""
def scrape_pbp(game_id):
    """
    TO DO
    """
    pass


"""
Shots (with location)
"""	
def pull_raw_shots(espn_game_id):
    """
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
	
    Coordinates correspond to feet (i.e. NBA court is 50ft x 94f).
    If you are standing behind the offensive team's hoop then
    the X axis runs from left to right and the Y axis runs from
    bottom to top. The center of the hoop is located at (25, 5.25).
    x=25 y=-2 and x=25 y=96 are free-throws (8ft jumpers).
    """
    page = requests.get('%s%s' % (ESPN_NBA_SHOT_URL, espn_game_id))
    xml = BeautifulSoup(page.text)
    return map(lambda x: x.attrs, xml.findAll('shot'))


def parse_shot_description(description):
    """
    Parse the shot descriptions e.g. Made 1ft jumper 11:40 in 1st Qtr
    """	
    pattern = re.compile('(\w+) (\d+)ft ([\w\d\-]+) ([\d\:]+) in (\d)\w+ (\w+)')
    m = re.match(pattern, description)
    if m is not None:
		return dict(zip([u'res',u'dist_ft',u'shot_type',u'gtime',u'per',u'per_type'], m.groups()))
    else:
		return dict()


def scrape_shots(game_id):
    """
    Scrape shot data from shot chart (e.g. x, y, result)
    """
    raw_shots = pull_raw_shots(game_id)
    parsed_shots = list()
    for shot in raw_shots:
        shot[u'game_id'] = game_id
        shot[u'shot_id'] = shot['id']
        shot = dict(shot, **parse_shot_description(shot['d']))
        # TO DO: Link this to schema.sql
        parsed_shots.append([shot[key] for key in ['shot_id','game_id','pid','p','t','gtime','qtr','res','dist_ft','shot_type','x','y']])
    return parsed_shots


def update_shot(db, game_ids):
    """
    Update the ESPN_NBA_SHOT table
    """    
    for game_id in game_ids:
    	shots = (scrape_shots(game_id))    	
    	db.executemany('INSERT INTO ESPN_NBA_BOX VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', shots)
    	db.commit()
        print 'Inserted gameId=%s into ESPN_NBA_SHOT at %s!' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
        sleep(random()*SLEEP_SEC)


def clean_shot(db):
    """
    Clean the raw ESPN_NBA_SHOT table based on quirks i have noticed in analysis
    """
    # These appear to be free-throws from cross-referencing with PBP
    db.execute('delete from espn_nba_shot where (y=-2 or y=96) and x=25')
    # TO DO: Remove back-to-back occurrences of x=25, y=6, dist_ft=0, same gtime from 08-09 and 09-10 (they are FTs)
    
    # Top/bottom code based on court dimensions (94 ft by 50 ft)
    db.execute('update espn_nba_shot set x = 0 where x<0')
    db.execute('update espn_nba_shot set x = 50 where x>50')
    db.execute('update espn_nba_shot set y = 0 where y<0')
    db.execute('update espn_nba_shot set y = 50 where y>94')
    db.commit()
