DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS board;
DROP TABLE IF EXISTS user_board;
DROP TABLE IF EXISTS board_task;
DROP TABLE IF EXISTS task;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  personal_board INTEGER UNIQUE,
  FOREIGN KEY (personal_board) REFERENCES board (id)
);

CREATE TABLE board (
  id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
  admin_id INTEGER,
  name TEXT NOT NULL,
  FOREIGN KEY (admin_id) REFERENCES user (id)
);

CREATE TABLE user_board (
  user_id INTEGER,
  board_id INTEGER, 
  FOREIGN KEY (user_id) REFERENCES user (id)
  FOREIGN KEY (board_id) REFERENCES board (id)
);

CREATE TABLE board_task (
  board_id INTEGER,
  task_id INTEGER,
  FOREIGN KEY (board_id) REFERENCES board (id)
  FOREIGN KEY (task_id) REFERENCES task (id)
);

CREATE TABLE task (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  priority_group TEXT NOT NULL,
  task TEXT NOT NULL,
  assignees TEXT NOT NULL
);