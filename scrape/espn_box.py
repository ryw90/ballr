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
SLEEP_SEC = 1 # Average number of seconds to sleep between hitting of web page

def scrape_box_ov(game_id):
    """
    Scrape game overview from box score e.g. date, coverage, attendance
    TO DO: 
        - FIX ISSUE WITH LENGTH (SHOULD BE 12, SOMETIMES 15)
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
    Scrape stats from box score e.g. date, coverage, attendance
    """
    plyr_string = re.compile(r'player')
    url = '%s%s' % (ESPN_NBA_BOX_URL, game_id)        
    page = requests.get(url)
    if page.url == url:
        soup = BeautifulSoup(page.text)
        box_lines = soup.findAll('tr', class_=plyr_string)
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

def update_table(db, game_ids):
    """
    Update the ESPN_NBA_SHOT table
    """
    box_ov = list()
    for game_id in game_ids:
        box_ov.append([game_id] + scrape_box_ov(game_id))
        print 'JUST SCRAPED BOX FOR %s at %s' % (game_id, strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
        sleep(random()*SLEEP_SEC)
    db.executemany('INSERT INTO ESPN_NBA_BOX_OV VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', box_ov)
    db.commit()
    print 'INSERTED %d RECORDS INTO ESPN_NBA_BOX_OV' % len(box_ov)

    # TO DO: RUN FROM HERE TO BOTTOM    
    for game_id in game_ids:
        box = map(lambda l: [game_id] + l, scrape_box(game_id))
        db.executemany('INSERT INTO ESPN_NBA_BOX VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', box)
        db.commit()
        print 'INSERTED %d RECORDS INTO ESPN_NBA_BOX_OV' % len(box)
        sleep(random()*SLEEP_SEC)

# game_ids = game_ids_2008to2009 + game_ids_2009to2010 + game_ids_2010to2011 + game_ids_2011to2012 + game_ids_2012to2013

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
    