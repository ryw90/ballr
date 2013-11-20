"""
Scrape ESPN.com for box score information

"""

import re as re
import requests as requests
import sys as sys
import sqlite3
from random import random
from time import sleep, gmtime, strftime
from bs4 import BeautifulSoup

import espn_master

ESPN_NBA_BOX_URL = 'http://sports.espn.go.com/nba/boxscore?gameId='
ESPN_NBA_BOX_COLS = ['shot_id','game_id','pid','p','t','gtime','qtr','res','dist_ft','shot_type','x','y'] # TO DO: Link this to Schema file
ESPN_GAME_IDS = {'2010-2011': (301026002, 310413030),
                 '2011-2012': (311225006, 320426030),
                 '2012-2013': (400277721, 400440940)}
SLEEP_SEC = 2 # Average number of seconds to sleep between hitting of web page

def scrape_box_ov(game_id):
    """
    Scrape game overview from box score e.g. date, coverage, attendance
    """
    url = '%s%s' % (ESPN_NBA_BOX_URL, game_id)        
    page = requests.get(url)
    if page.url == url:
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
            for key in ['Officials', 'Attendance', 'Time of Game']:
                m = re.search(r'%s:\s*</strong>\s*([\w\,\:\s]+)\s*<br>' % key, page.text)
                if m is not None:
                    box_ov.append(m.group(1))
                else:
                    box_ov.append(None)
            box_ov[9] = box_ov[9].replace(',','') # Scrub attendance
        except:
            box_ov.extend([None, None, None])
                 
        return box_ov

def scrape_box(game_id):
    """
    Scrape stats from box score e.g. date, coverage, attendance
    - TO DO
    """
    pass

def update_table(db, game_ids):
    """
    Update the ESPN_NBA_SHOT table
    """
    box_ov = list()
    for game_id in game_ids:
        # box.append([game_id] + scrape_box(game_id))
        box_ov.append([game_id] + scrape_box_ov(game_id))
        print 'JUST SCRAPED BOX FOR %s at %s' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
        sleep(random())
    db.executemany('INSERT INTO ESPN_NBA_BOX_OV VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', box_ov)
    print 'INSERTED %d RECORDS INTO ESPN_NBA_BOX_OV' % len(box_ov)    

if __name__=='__main__':
    """
    For running from terminal...
    Usage: python espn_box.py "[date]" "[db_path]"
    """	
    date, db_path = sys.argv[1:3] # The path is currently "../core-data.db"
    db = sqlite3.connect('db_path') # TO DO: Store DB_PATH in a CONFIG file    
    game_ids = espn_master.scrape_game_ids(date) # TO DO: Set this up to run every day
    update_table(db, game_ids)
    db.close()
    