BEGIN TRANSACTION;
DELETE FROM "user" WHERE "id" = 1;
INSERT INTO "user" ("id","username","password","is_admin") VALUES (1,'test','pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f',1),
 (2,'user','pbkdf2:sha256:150000$hbBby0iJ$e1f79fe2d4b25315b7e278de1d2f195124d1a1f514aabb4187b46a52b6db9b30',0),
 (3,'other','pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79',1);
INSERT INTO "answer_options" ("id","text") VALUES (1,'option1'),
 (2,'option2'),
 (3,'option3'),
 (4,'option3');
INSERT INTO "questions" ("id","answer_id","text") VALUES (1,1,'Test Question');
INSERT INTO "question_answer_rel" ("question_id","answer_option_id") VALUES (1,1),
 (1,2),
 (1,3),
 (1,4);
INSERT INTO "quizzes" ("id","name","author_id") VALUES (1,'Test Index Quiz',1);
INSERT INTO "quiz_question_rel" ("quiz_id","question_id") VALUES (1,1);
INSERT INTO "quiz_result" ("id","user_id","quiz_session_id","quiz_id","question_id","answer_id") VALUES (1,2,1,1,1,2);
COMMIT;
