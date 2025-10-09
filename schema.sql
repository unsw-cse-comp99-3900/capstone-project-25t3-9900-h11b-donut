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

CREATE TABLE IF NOT EXISTS courses (
  course_code VARCHAR(16) PRIMARY KEY,
  course_name VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS student_courses (
  student_id  VARCHAR(32)  NOT NULL,
  course_code VARCHAR(16)  NOT NULL,
  PRIMARY KEY (student_id, course_code),
  CONSTRAINT fk_sc_student FOREIGN KEY (student_id) REFERENCES student_accounts(student_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_sc_course FOREIGN KEY (course_code) REFERENCES courses(course_code)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- course material
CREATE TABLE IF NOT EXISTS materials (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_code VARCHAR(16) NOT NULL,
  title VARCHAR(255) NOT NULL,
  url   VARCHAR(1024) NOT NULL,
  CONSTRAINT fk_mat_course FOREIGN KEY (course_code) REFERENCES courses(course_code)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS student_weekly_preferences (
  student_id           VARCHAR(32)  NOT NULL,
  semester_code        VARCHAR(20)  NOT NULL,             -- term : '2025T1'
  week_no              TINYINT      NOT NULL,             -- 1..10
  daily_hours          DECIMAL(4,2) NOT NULL,             -- how many hours one will study per day
  weekly_study_days    TINYINT      NOT NULL,             -- how many days one will study per week
  avoid_days_bitmask   TINYINT UNSIGNED NOT NULL DEFAULT 0,  -- Mon=1, Tue=2, …, Sun=64
  mode                 ENUM('manual','default') NOT NULL DEFAULT 'manual',
  derived_from_week_no TINYINT NULL,                      -- default : =week_no-1；manual : NULL
  created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (student_id, semester_code, week_no),
  CONSTRAINT fk_prefs_student FOREIGN KEY (student_id)
    REFERENCES student_accounts(student_id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CHECK (week_no BETWEEN 1 AND 10),
  CHECK (daily_hours >= 0 AND daily_hours <= 24),
  CHECK (weekly_study_days BETWEEN 0 AND 7),
  CHECK (
    (mode = 'manual'  AND derived_from_week_no IS NULL) OR
    (mode = 'default' AND derived_from_week_no = week_no - 1)
  )
) ENGINE=InnoDB;
