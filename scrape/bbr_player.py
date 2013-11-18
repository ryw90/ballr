"""
Scrape basketball-reference.com (also sports-reference.com for college basketball) for player information

TO DO:
    - Just use sqlite3 instead of this dataset stuff, not worth the hassle
    
"""

from bs4 import BeautifulSoup
from time import sleep, gmtime, strftime
from requests import get
from random import random
import re as re
import string as string
import pandas as pd

BBR_NBA_URL = 'http://www.basketball-reference.com' ## TO DO: MOVE THESE INTO A CONFIG FILE 
BBR_NBA_DETS = ['Twitter', 'Position', 'Shoots', 'Height', 'Weight', 'Born', 'High School', 'College', 'Draft', 'NBA Debut', 'Hall of Fame']
BBR_NBA_DETS_HDRS = dict(zip(BBR_NBA_DETS, map(lambda x: string.lower(x.replace(' ','_') + '_dets'), BBR_NBA_DETS)))
SLEEP_SECS = 2 # Average number of seconds to sleep between hitting of web page

def scrape_nba_basic_all(sleep_secs=SLEEP_SECS):
    """
    Scrape basic player information from alphabetical player lists e.g. name, position, height, weight, player_id (unique to basketball-reference)
    Input:
        NA
    Output:
        Return a dictionary with information for each player
    """
    print 'Expected runtime: %d minutes starting %s' % (round(len(string.ascii_lowercase)*SLEEP_SECS/60.), strftime("%d %b %Y %H:%M:%S +0000", gmtime()))
    player_info_basic = list()   
    for letter in string.ascii_lowercase: 
        page = get('%s/players/%s' % (BBR_NBA_URL, letter))
        if 'errors' in page.url:
            print 'players/' + letter + ' not found... moving on...'
        else:
            player_table_page = BeautifulSoup(page.text)
            player_table = player_table_page.find('table', attrs={'id':'players'}).findAll('tr')
            player_table_headers = [string.lower(header).replace(' ', '_') for header in extract_tag_text(player_table[0], 'th')]
            player_info_basic_tmp = [dict(zip(player_table_headers + [u'bbr_id'], # headers
                                              extract_tag_text(tr, 'td') + [tr.find('a')['href']]) # player info
                                            ) for tr in player_table[1:]]
            player_info_basic += player_info_basic_tmp
        sleep(random()*SLEEP_SECS)       
    return player_info_basic   

def scrape_nba_detailed_many(player_ids, log=True):
    """
    Scrape detailed player information for a list of players, this can be quite slow
    Input:
        A list of player_ids of the form /players/[letter]/[player_id]
    Output:
        A list of player information dicts for each player
    """
    print 'Expected runtime: %d minutes starting %s' % (round(len(player_ids)*SLEEP_SECS/60.), strftime("%d %b %Y %H:%M:%S +0000", gmtime()))
    player_info_detailed = list()
    for player in player_ids:
        details = scrape_nba_detailed_one(player)
        details['bbr_id'] = player
        player_info_detailed.append(details)
        sleep(random()*SLEEP_SECS)        
        if log:
            print 'Scraped %s at %s' % (player, strftime("%d %b %Y %H:%M:%S +0000", gmtime()))        
    return player_info_detailed       

def scrape_nba_detailed_one(player_ext):
    """
    Scrape detailed player information from a player's personal page
    Input:
        An extension of the form /players/[letter]/[player_id]
    Output:
        A dict of player information e.g. Twitter handle, Position, etc.
    """                     
    details = dict()
    page = get('%s%s' %(BBR_NBA_URL, player_ext))
    if 'errors' in page.url:
        print player_ext + ' not found'        
    else:        
        player_page = BeautifulSoup(page.text)
        for detail in BBR_NBA_DETS:
            result = re.search(r'%s: ([\w\d\-,()\'\. ]+)' % detail, player_page.text, flags=re.UNICODE) ## TO DO: Make this REGEX ROBUST
            if result:
                details[BBR_NBA_DETS_HDRS[detail]] = result.group(1)
    return details

def extract_tag_text(html, tag):
    """
    Given a BeautifulSoup substring of HTML and tag of interest, extract the text value(s) associated with the tag
    """
    return [string.text for string in html.findAll(tag)]  

def parse_nba_draft_dets(string):
    """
    TO DO
    """
    pattern = re.compile('([\w\s]+), (?:(\d+)\w+ round \((\d+)\w+ pick, (\d+)\w+ overall\), )?(\d+) NBA Draft')
    m = re.search(pattern, string)
    if m is not None:
        return list(m.groups())

def parse_nba_hof_dets(string):
    """
    TO DO
    """
    hof_dets = dict()
    for substr in string.split('and'):
        m = re.search('as (\w+) in (\d+)', substr)
        if m is not None:
            hof_dets[m.group(1)] = m.group(2)            
    return hof_dets        

def combine_basic_detailed(basic, detailed):
    """
    Combine the basic and detailed player information from BBR
    Input:
        basic - dict of basic player info (identified by bbr_id)
        detailed - dict of detailed player info (also identified by bbr_id)
    Output:
        A dict that has parsed certain keys and removed redundant keys
    """
    combined = pd.merge(pd.DataFrame(basic), pd.DataFrame(detailed), how='outer', on='bbr_id')    
    # Parse birth date and location
    tmp_born = pd.DataFrame([str(x).split(' in ') for x in combined['born_dets']]) # TO DO: Make this less hard-coded
    combined['birth_date'], combined['birth_loc'] = tmp_born.ix[:,0].str.strip(), tmp_born.ix[:,1].str.strip()
    # Convert height to inches
    combined['height_in'] = combined['height_dets'].str.split('-').apply(lambda x: int(x[0])*12 + int(x[1]))
    # Parse draft details
    tmp_draft = combined.draft_dets[pd.notnull(combined.draft_dets)].apply(parse_nba_draft_dets).apply(pd.Series)
    tmp_draft.columns = ['draft_team','draft_round','draft_pick_round','draft_pick_overall', 'draft_year']
    combined = combined.join(tmp_draft)
    # Parse Hall of Fame details
    tmp_hof = combined.hall_of_fame_dets[pd.notnull(combined.hall_of_fame_dets)].apply(parse_nba_hof_dets).apply(pd.Series)
    tmp_hof.rename(columns={'Coach':'hof_coach','Contributor':'hof_contributor','Player':'hof_player'}, inplace=True)
    combined = combined.join(tmp_hof)
    # Return parsed/non-redundant columns
    combined.rename(columns={'pos':'position','wt':'weight_lbs','high_school_dets':'high_school','nba_debut_dets':'nba_debut','shoots_dets':'shoots'}, inplace=True)
    combined = combined[['bbr_id',
                         'college',
                         'player',
                         'position',
                         'shoots',
                         'weight_lbs',
                         'height_in',
                         'birth_date',
                         'birth_loc',
                         'draft_team',
                         'draft_round',
                         'draft_pick_overall',
                         'draft_year',
                         'high_school',
                         'nba_debut']]
    return [dict(row) for idx, row in combined.iterrows()]

def update_table(db):
    """
    Update the BBR player table
    Input:
        A dataset table for BBR player information
    Output:
        ???
    """
    ### Start with NBA players
    nba_basic = scrape_nba_basic_all()
    nba_detailed = scrape_nba_detailed_many([plyr['bbr_id'] for plyr in nba_basic])
    nba_combined = combine_basic_detailed(nba_basic, nba_detailed)
    db['BBR_NBA_PLAYER'].insert_many(nba_combined) # TO DO: Switch to sqlite3 for more control
    print 'Inserted %d records into BBR_NBA_PLAYER!' % len(nba_combined)
    ### TO DO: NBDL players
    ### TO DO: CBB players
    