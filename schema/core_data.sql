CREATE TABLE BBR_NBA_PLAYER (
    bbr_id TEXT PRIMARY KEY NOT NULL,
    player TEXT,
    birth_date TEXT,
    birth_loc TEXT,
    height_in INTEGER,
    weight_lbs INTEGER,
    position TEXT,
    shoots TEXT,
    high_school TEXT,
    college TEXT,    
    draft_year INTEGER,
    draft_round INTEGER,
    draft_team TEXT,
    draft_pick_overall INTEGER,
    nba_debut TEXT
);

CREATE TABLE ESPN_NBA_SHOT (
    shot_id INTEGER PRIMARY KEY NOT NULL,
    game_id INTEGER NOT NULL,
    pid INTEGER,
    p TEXT,
    t TEXT,
    gtime TEXT,
    qtr INTEGER,
    res TEXT,
    dist_ft INTEGER,
    shot_type TEXT,   
    x INTEGER,
    y INTEGER
);

CREATE TABLE ESPN_NBA_BOX_OV (
    game_id INTEGER PRIMARY KEY NOT NULL,
    away_team TEXT,
    away_score INTEGER,
    home_team TEXT,
    home_score INTEGER,
    game_time_et TEXT,
    game_date TEXT,
    arena TEXT,
    coverage TEXT,
    officials TEXT,
    attendance INTEGER,
    duration INTEGER,
);

