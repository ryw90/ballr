create view ESPN_NBA_SHOT_AGG as
	select
		pid, p, x, y,
		count(*) as shot_freq
	from (
		select 
			pid, p, x,
			case
				when t = "h" then 97 - y
				else y
			end as y
		from ESPN_NBA_SHOT
		where pid <> ''
	)
	group by pid, p, x, y;

create view	ESPN_NBA_PER_GAME as
	select
		pid, player, pos,
		count(game_id) as gp,
		round(avg(mins), 1) as mins,
		round(avg(reb), 1) as reb,
		round(avg(ast), 1) as ast,
		round(avg(blk), 1) as blk,
		round(avg(stl), 1) as stl,
		round(avg(tos), 1) as tos,
		round(avg(pts), 1) as pts		
	from ESPN_NBA_BOX
	where mins <> '' and game_id <> '400436572'
	group by pid, player, pos;

# TO DO:
# - Delete rows with no minutes
# - Delete rows for all star games
#   asg = []
