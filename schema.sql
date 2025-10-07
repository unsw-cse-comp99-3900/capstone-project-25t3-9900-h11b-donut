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