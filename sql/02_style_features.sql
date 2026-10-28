SELECT
    e.PLAYER_ID,
    e.PLAYER_NAME,
    e.POSS,
    b.FGA,
    b.FG3A,
    b.STL,
    b.BLK,
    a.USG_PCT,
    poss.TOUCHES,
    poss.AVG_SEC_PER_TOUCH,
    pass.PASSES_MADE,
    pass.POTENTIAL_AST,
    drv.DRIVES,
    shot.RA_FGA,
    pull.PULL_UP_FGA,
    score.PCT_UAST_FGM,
    cs.CATCH_SHOOT_FG3A,
    paint.PAINT_TOUCHES,
    post.POST_TOUCHES,
    hust.SCREEN_ASSISTS,
    hust.DEFLECTIONS,
    hust.CONTESTED_SHOTS,
    hust.CONTESTED_SHOTS_3PT,
    hust.CONTESTED_SHOTS_2PT,
    reb.OREB_CHANCES,
    reb.DREB_CHANCES

FROM eligible_players AS e

LEFT JOIN base_stats AS b
    ON e.PLAYER_ID = b.PLAYER_ID

LEFT JOIN advanced_stats AS a
    ON e.PLAYER_ID = a.PLAYER_ID

LEFT JOIN possessions_stats AS poss
    ON e.PLAYER_ID = poss.PLAYER_ID

LEFT JOIN passing_stats AS pASs
    ON e.PLAYER_ID = pass.PLAYER_ID

LEFT JOIN drives_stats AS drv
    ON e.PLAYER_ID = drv.PLAYER_ID

LEFT JOIN shot_locations AS shot
    ON e.PLAYER_ID = shot.PLAYER_ID

LEFT JOIN pullupshot_stats AS pull
    ON e.PLAYER_ID = pull.PLAYER_ID

LEFT JOIN scoring_stats AS score
    ON e.PLAYER_ID = score.PLAYER_ID

LEFT JOIN catchshoot_stats AS cs
    ON e.PLAYER_ID = cs.PLAYER_ID

LEFT JOIN painttouch_stats AS paint
    ON e.PLAYER_ID = paint.PLAYER_ID

LEFT JOIN posttouch_stats AS post
    ON e.PLAYER_ID = post.PLAYER_ID

LEFT JOIN hustle_stats AS hust
    ON e.PLAYER_ID = hust.PLAYER_ID

LEFT JOIN rebounding_stats AS reb
    ON e.PLAYER_ID = reb.PLAYER_ID;