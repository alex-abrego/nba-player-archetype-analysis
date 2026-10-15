SELECT
    b.PLAYER_ID,
    b.PLAYER_NAME,
    b.TEAM_ABBREVIATION,
    b.AGE,
    b.GP,
    b.MIN,
    a.POSS
FROM base_stats AS b
LEFT JOIN advanced_stats AS a
    ON b.PLAYER_ID = a.PLAYER_ID
WHERE b.MIN >= $MIN_MINUTES