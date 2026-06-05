-- ============================================================
--  BASKETBALL PLAYERS DBMS MINI PROJECT 
--  2 teams, 5 players each, tracking minutes played & points scored.
--  Run this whole file once in MySQL Workbench / CLI.
-- ============================================================

DROP DATABASE IF EXISTS basketball_db;
CREATE DATABASE basketball_db;
USE basketball_db;

-- ------------------------------------------------------------
--  TABLE 1 : teams  (the "one" side)
-- ------------------------------------------------------------
CREATE TABLE teams (
    team_id      INT AUTO_INCREMENT PRIMARY KEY,
    team_name    VARCHAR(100) NOT NULL UNIQUE,
    city         VARCHAR(100),
    coach        VARCHAR(100),
    player_count INT DEFAULT 0          -- kept in sync by triggers
);

-- ------------------------------------------------------------
--  TABLE 2 : players  (the "many" side -> FK to teams)
-- ------------------------------------------------------------
CREATE TABLE players (
    player_id      INT AUTO_INCREMENT PRIMARY KEY,
    player_name    VARCHAR(100) NOT NULL,
    team_id        INT,
    position       VARCHAR(40),       -- PG, SG, SF, PF, C
    jersey_number  INT,
    minutes_played INT DEFAULT 0,
    points_scored  INT DEFAULT 0,
    CONSTRAINT fk_team
        FOREIGN KEY (team_id) REFERENCES teams(team_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ------------------------------------------------------------
--  TABLE 3 : player_audit  (filled automatically by a trigger)
-- ------------------------------------------------------------
CREATE TABLE player_audit (
    audit_id    INT AUTO_INCREMENT PRIMARY KEY,
    player_id   INT,
    player_name VARCHAR(100),
    action      VARCHAR(20),
    action_time DATETIME
);

-- ============================================================
--  TRIGGERS
-- ============================================================
DELIMITER //

-- When a player is added, bump the team's player_count.
CREATE TRIGGER trg_after_player_insert
AFTER INSERT ON players
FOR EACH ROW
BEGIN
    IF NEW.team_id IS NOT NULL THEN
        UPDATE teams
           SET player_count = player_count + 1
         WHERE team_id = NEW.team_id;
    END IF;

    INSERT INTO player_audit (player_id, player_name, action, action_time)
    VALUES (NEW.player_id, NEW.player_name, 'INSERT', NOW());
END//

-- When a player is removed, lower player_count and log it.
CREATE TRIGGER trg_after_player_delete
AFTER DELETE ON players
FOR EACH ROW
BEGIN
    IF OLD.team_id IS NOT NULL THEN
        UPDATE teams
           SET player_count = GREATEST(player_count - 1, 0)
         WHERE team_id = OLD.team_id;
    END IF;

    INSERT INTO player_audit (player_id, player_name, action, action_time)
    VALUES (OLD.player_id, OLD.player_name, 'DELETE', NOW());
END//

DELIMITER ;

-- ============================================================
--  STORED PROCEDURES
-- ============================================================
DELIMITER //

-- Aggregate stats for a single team (AVG / MAX / COUNT).
CREATE PROCEDURE GetTeamStats(IN p_team_id INT)
BEGIN
    SELECT  t.team_name,
            COUNT(p.player_id)            AS total_players,
            ROUND(AVG(p.points_scored),2) AS avg_points,
            ROUND(AVG(p.minutes_played),1)AS avg_minutes,
            MAX(p.points_scored)          AS top_score
      FROM  teams t
      LEFT JOIN players p ON p.team_id = t.team_id
     WHERE  t.team_id = p_team_id
     GROUP BY t.team_id, t.team_name;
END//

-- League-wide top scorers (JOIN + ORDER BY + LIMIT).
CREATE PROCEDURE GetTopScorers(IN p_limit INT)
BEGIN
    SELECT  p.player_name,
            t.team_name,
            p.position,
            p.points_scored
      FROM  players p
      JOIN  teams   t ON p.team_id = t.team_id
     ORDER BY p.points_scored DESC
     LIMIT  p_limit;
END//

DELIMITER ;

-- ============================================================
--  VIEW : player roster with team name (JOIN logic reused by API)
-- ============================================================
CREATE VIEW v_player_roster AS
SELECT  p.player_id,
        p.player_name,
        t.team_name,
        p.position,
        p.jersey_number,
        p.minutes_played,
        p.points_scored
  FROM  players p
  LEFT JOIN teams t ON p.team_id = t.team_id;

-- ============================================================
--  SAMPLE DATA
-- ============================================================
INSERT INTO teams (team_name, city, coach) VALUES
('Lakers',   'Los Angeles',  'Darvin Ham'),
('Warriors', 'San Francisco','Steve Kerr');

-- team_id values follow the insert order above (1..2)
INSERT INTO players
(player_name, team_id, position, jersey_number, minutes_played, points_scored) VALUES
('LeBron James',  1, 'SF', 23, 35, 26),
('Anthony Davis', 1, 'PF', 3,  33, 25),
('Austin Reaves', 1, 'SG', 15, 30, 16),
('DAngelo Russell',1,'PG', 1,  28, 18),
('Rui Hachimura', 1, 'PF', 28, 25, 13),
('Stephen Curry', 2, 'PG', 30, 34, 27),
('Klay Thompson', 2, 'SG', 11, 31, 18),
('Andrew Wiggins',2, 'SF', 22, 30, 17),
('Draymond Green',2, 'PF', 23, 29, 9),
('Kevon Looney',  2, 'C',  5,  22, 7);
