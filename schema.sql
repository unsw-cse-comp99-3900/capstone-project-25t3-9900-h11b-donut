CREATE DATABASE IF NOT EXISTS ai_learning_coach
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE ai_learning_coach;

CREATE TABLE IF NOT EXISTS student_accounts (
  student_id     VARCHAR(32)  NOT NULL,
  email          VARCHAR(254) NOT NULL,
  password_hash  CHAR(60)     NOT NULL,
  PRIMARY KEY (student_id),
  UNIQUE KEY uq_email (email)
);
