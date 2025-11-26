# 1. What we test

## 1.1 Unit tests validate core logic, edge cases, and input validation.
`test_auth.py`

---

## **1. Login API**

Unit tests cover both successful and failure scenarios, including:

- Successful login with valid credentials  
- Incorrect password → **401**  
- Missing parameters  
- Login with nonexistent student ID  
- Ensuring no token is issued when authentication fails  
- Verifying that `current_token` and `token_issued_at` are correctly updated  

---

## **2. Registration API**

Unit tests validate input-parsing logic, validation rules, and error handling:

- Successful registration (JSON body and validation flow)  
- Duplicate student ID → **409**  
- Duplicate email → **409**  
- Missing fields (student ID, email, name, password)  
- Invalid email format  
- Invalid password that fails project validation rules  
- `ValidationError` propagation  
- Database integrity errors  

These tests ensure that the authentication subsystem behaves deterministically, rejects malformed input, and adheres to all project-defined validation requirements.

---

# `test_course_task.py`

## **1. Task Creation**

Unit tests verify:

- Successful creation of tasks under a course  
- Proper handling of task metadata such as title, brief, deadline, and percent contribution  
- Validation of percent contribution values  

---

## **2. Deadline Validation (Edge Case)**

Tests ensure:

- Tasks with deadlines in the past are correctly rejected  
- Backend logic correctly parses datetime strings  
- Temporal validation rules are strictly enforced  

---

## **3. Course Deletion & Cascade Cleanup**

When a course is deleted, tests confirm that:

- All associated `CourseTask` records are removed  
- All related `TaskProgress` entries are cleaned up  
- No orphan progress objects remain  
- Referential integrity is consistently maintained  

---

## **4. Student Enrollment — Non-existent Course (Edge Case)**

Tests verify that:

- Enrollment attempts for nonexistent courses are rejected  
- `/courses/add` returns **404** with the expected message `"Course not found"`  
- No `StudentEnrollment` record is created under invalid course codes  
- Backend validation handles incorrect or malformed input robustly  

---

## **5. Student Enrollment — Duplicate Enrollment Prevention**

Unit tests ensure that:

- Re-enrolling into the same course does not create duplicate `StudentEnrollment` entries  
- The endpoint returns **200** with message `"already enrolled"`  
- Database uniqueness constraints on `(student_id, course_code)` hold correctly  
- Redundant state updates and inconsistent user experience are prevented  

---

These tests collectively ensure that the course, enrollment, and task-management subsystem behaves predictably under both normal and exceptional scenarios. They verify that invalid configurations are rejected, duplicate or inconsistent states are prevented, and that data integrity is consistently maintained during operations such as task creation, enrollment attempts, and full course removal.
