# 1. What we test

## 1.1 Unit tests validate core logic, edge cases, and input validation.
# `test_auth.py`

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

# 2. Alignment With Project Testing Guidelines

| Guideline                      | Our Coverage                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|
| **Unit tests**                | Authentication, course mgmt, task mgmt, enrollment APIs                      |
| **Integration tests**         | Course–Task cascade deletion, enrollment + materials retrieval               |
| **Edge cases**                | Past deadlines, duplicated enrollment, nonexistent courses, invalid payload   |
| **Mocking external libs**     | Gemini LLM API, HTTP endpoints (`requests.post`)                             |
| **Data validation**           | Missing fields, invalid datetime, malformed JSON                             |
| **Business logic**            | Enrollment uniqueness, deadline rules, cascade progress cleanup               |
| **Error handling**            | Auth failure, 400 input errors, 404 not found, 409 duplication logic         |
| **Race conditions**           | N/A (admin operations are atomic via `transaction.atomic`)                   |
| **If automated tests impossible** | N/A — all APIs testable through Django test client                         |

The backend test suite fully aligns with project testing expectations and covers both functional and robustness requirements.


# 3. How to Run Test

```bash
cd django_backend

cd test

python manage.py test test.test_course_task 

python manage.py test test.test.test_auth  

python test_plan_api_with_mocks.py #mock data stores in mock_test_results.json

python test_ai_unified.py # test all the functionalities related to AI 

```

---
# 4. Manual Testing Procedures (When Automated Tests Are Not Possible)
Although most features of this project can be tested using Django’s automated test framework, certain cross-layer or end to end behaviours cannot be fully validated through automated tests alone. These include scenarios that depend on real UI interactions, asynchronous background jobs (cron), and multi-endpoint data consistency.  
Therefore, the following **manual system testing procedures** are provided to ensure correctness in situations where automated tests are insufficient. We present several representative test cases as examples of how these scenarios are validated.

---

## **4.1 Student Progress Update Flow — Manual UI Test**

**Purpose:**  
Verify that when a student marks a task part as completed, their progress bar updates correctly and the admin-side progress trend view reflects the change.

**Test Steps:**
1. Log in as a student and open the Study Plan page.  
2. Tick any task part to mark it as completed.  
3. Observe whether the student-side progress bar updates immediately.  
4. Log in as an admin and open the “Progress Trend” page.  
5. Confirm the progress value for that student has been updated.  
6. Inspect the database to ensure the `task_progress` table stores the correct updated value.

**Expected Result:**  
- The progress bar updates instantly.  
- The admin dashboard shows the updated progress.  
- Progress records in the database are accurate and synchronized.

---

## **4.2 Overdue Auto-Detection and Race Condition Handling**

**Purpose:**  
Verify that when the automatic overdue detection job is about to run, a student manually marking a task as completed a few seconds before does not cause incorrect overdue counts due to transmission delay.

**Test Steps:**
1. Set a task deadline close to the current time.  
2. Wait for (or manually trigger) the overdue detection cron task.  
3. Within the final 5 seconds before cron runs, have the student check “completed”.  
4. Open the admin risk dashboard.  
5. Cross-check the overdue count with the data stored in `reminder_duereport`.

**Expected Result:**  
- If the student completed the task before the deadline, the overdue count should remain 0.  
- Network latency or UI → backend transmission delay should not cause the student to be incorrectly marked overdue.  
- The overdue count in the admin dashboard must match the database record exactly.

---

## **4.3 Course Deletion Consistency Test**

**Purpose:**  
Ensure that if an admin deletes a course, the student-side plan containing tasks from that course does not produce invalid writes or dirty data when the student interacts with the old plan.

**Test Steps:**
1. Have a student generate a weekly plan that includes Course A.  
2. Delete Course A from the admin panel.  
3. Return to the student’s weekly plan page and continue marking parts from the deleted course.  
4. Verify the database integrity:  
   - `task_progress` should not write progress for deleted tasks.  
   - `study_plan_item` should remain consistent.  
   - No orphaned or invalid records should be created.

**Expected Result:**  
- Student-side interactions do not cause errors.  
- No dirty or orphaned data is generated.  
- Deleted tasks are not re-created or updated in the database.  
- Admin-side dashboards remain consistent.

---

## **Summary**

These manual testing procedures validate system behaviours that cannot be reliably tested through automation alone. They ensure:

- Real-time student progress synchronization  
- Correct overdue detection even under timing-sensitive conditions  
- Strong data consistency when courses or tasks are removed  
- No dirty data, no invalid writes, and no incorrect analytics  

Together, these tests guarantee the robustness, reliability, and correctness of the system in real-world usage scenarios.

# 5. Limitations 

- when running test file: it may take a long time which may be 1min at most
- but it can generate the test result finally
- due to time limitation our team didn't figure out what leads to that case
- in future our team will try to solve it