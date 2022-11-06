INSERT INTO board (admin_id, name)
VALUES
  (1, "test's Personal Board"),
  (2, "other's Personal Board"),
  (3, "three's Personal Board"),
  (3, "General Board"),
  (1, "dummy board");

INSERT INTO user (username, password, personal_board)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 1),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79', 2),
  ('three', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79', 3);


INSERT INTO user_board (user_id, board_id)
VALUES
    (1, 1),
    (2, 2),
    (3, 3),
    (1, 4),
    (2, 4),
    (3, 4),
    (1, 5),
    (2, 1);

