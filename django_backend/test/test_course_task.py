# django_backend/test/test_course_task.py

import json
from datetime import timedelta
from courses.models import CourseCatalog, StudentEnrollment
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from stu_accounts.models import StudentAccount
from courses_admin.models import CourseAdmin
from courses.models import CourseTask
from task_progress.models import TaskProgress
from adm_accounts.models import AdminAccount
from courses_admin.views import delete_course
from courses.views import add_course


class CourseTaskTests(TestCase):
    def setUp(self):
        """
        Test setup:
        - Create an AdminAccount (required by CourseAdmin.admin_id foreign key)
        - Create a CourseCatalog entry
        - Create a CourseAdmin relationship record
        - Initialize a RequestFactory to manually construct request objects
        """
        self.factory = RequestFactory()
        self.admin_id = "admin001"

        # Create an admin account according to the foreign key constraints
        self.admin = AdminAccount.objects.create(
            admin_id=self.admin_id,
            email="admin@example.com",
            full_name="Test Admin",
            password_hash="dummy-hash",
        )

        self.course_code = "COMP4444"
        self.course = CourseCatalog.objects.create(
            code=self.course_code,
            title="Test Course",
            description="For testing",
        )

        # Establish the admin–course relationship
        CourseAdmin.objects.create(
            admin_id=self.admin_id,
            code=self.course,
        )

    def _admin_login(self):
        """
        Helper method to simulate an authenticated admin by:
        - Creating an admin account
        - Assigning a token
        - Injecting Authorization header for subsequent client requests
        """

        admin = AdminAccount.objects.create(
            admin_id="A001",
            email="admin@test.com",
            full_name="Admin",
            password_hash="dummy"
        )

        token = "test_admin_token"
        admin.current_token = token
        admin.save(update_fields=["current_token"])

        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    # ---------------------------------------------------
    # 1) Creating a task: rejection if not authenticated
    # ---------------------------------------------------
    def test_create_task_requires_auth(self):
        """
        /courses_admin/<course_id>/tasks/create

        This endpoint has admin authentication middleware.
        If not authenticated, the request should return 401/403.
        This test verifies that authorization is required.
        """
        url = reverse("create_tasks", args=[self.course_code])

        future_deadline = (timezone.localtime() + timedelta(days=3)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        payload = {
            "title": "Task 1",
            "deadline": future_deadline,
            "brief": "Some brief",
            "percent_contribution": 30,
        }

        resp = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Both 401 and 403 are acceptable for unauthorized access
        self.assertIn(resp.status_code, (401, 403))

    # ------------------------------------------------------------------
    # 2) Course deletion: cascade deletion of CourseTask + TaskProgress
    # ------------------------------------------------------------------
    def test_delete_course_cascade_tasks_and_progress(self):
        """
        delete_course behavior:
        - Deletes CourseCatalog
        - Deletes related CourseTask entries
        - Deletes TaskProgress entries (cascade cleanup)
        """
        # Create a task for this course
        task = CourseTask.objects.create(
            course_code=self.course_code,
            title="Cascade Task",
            deadline=timezone.localtime() + timedelta(days=5),
            brief="Will be deleted",
            percent_contribution=20,
        )

        # Create a TaskProgress entry for this task
        TaskProgress.objects.create(
            student_id="z1234567",
            task_id=task.id,
            progress=50,
        )

        # Confirm the TaskProgress exists
        self.assertEqual(TaskProgress.objects.filter(task_id=task.id).count(), 1)

        payload = {
            "admin_id": self.admin_id,
            "code": self.course_code,
        }

        # Use RequestFactory to construct a POST request and call delete_course directly
        request = self.factory.post(
            "/courses_admin/delete_course",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = delete_course(request)
        self.assertEqual(response.status_code, 200)

        # Course deleted
        self.assertFalse(
            CourseCatalog.objects.filter(code=self.course_code).exists()
        )
        # CourseTask deleted
        self.assertFalse(CourseTask.objects.filter(id=task.id).exists())
        # TaskProgress deleted
        self.assertEqual(TaskProgress.objects.filter(task_id=task.id).count(), 0)

    # ------------------------------------------------------------------
    # 3) Creating a task: reject deadlines in the past
    # ------------------------------------------------------------------
    def test_create_task_rejects_past_deadline(self):
        """
        Creating a task with a past deadline should return 400
        and an error message containing "deadline".
        """
        self._admin_login()

        url = reverse("create_tasks", args=[self.course_code])

        past_deadline = (timezone.localtime() - timedelta(days=1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        payload = {
            "title": "Invalid Task",
            "deadline": past_deadline,
            "brief": "should fail",
            "percent_contribution": 20,
        }

        resp = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertIn("deadline", resp.json().get("message", "").lower())


# ======================================================================
# AddCourse API Tests
# ======================================================================

class AddCourseApiTests(TestCase):
    def setUp(self):
        """
        Simulate a logged-in student by:
        - Storing a current_token in StudentAccount
        - Providing Authorization: Bearer <token> for all requests
        """
        self.factory = RequestFactory()

        self.token = "test-token-123"
        self.student_id = "z1234567"

        self.student = StudentAccount.objects.create(
            student_id=self.student_id,
            email=f"{self.student_id}@unsw.edu.au",
            name="Test Student",
            password_hash="dummy-hash",
            current_token=self.token,
        )

    def _post_add_course(self, course_code: str):
        """
        Helper method: construct a POST request with Authorization header
        and directly call the add_course view function.
        """
        payload = {"courseId": course_code}

        request = self.factory.post(
            "/api/courses/add",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        response = add_course(request)
        return response

    # ------------------------------------------------------------------
    # 1) Student attempts to add a nonexistent course
    # ------------------------------------------------------------------
    def test_add_nonexistent_course(self):
        """
        When a student attempts to add a course that does not exist:
        - Should return 404
        - message = "Course not found"
        """
        code = "COMP9999"

        self.assertFalse(CourseCatalog.objects.filter(code=code).exists())

        resp = self._post_add_course(code)

        self.assertEqual(resp.status_code, 404)
        body = json.loads(resp.content.decode("utf-8"))

        self.assertFalse(body.get("success"))
        self.assertEqual(body.get("message"), "Course not found")

    # ------------------------------------------------------------------
    # 2) Student trying to add a course they already enrolled in
    # ------------------------------------------------------------------
    def test_add_duplicate_course(self):
        """
        When a student has already enrolled in a course:
        - Should not raise an error
        - Should return 200
        - message = "already enrolled"
        - Database should still contain exactly one StudentEnrollment record
        """
        code = "COMP1234"

        CourseCatalog.objects.create(
            code=code,
            title="Test Course",
            description="For duplicate enroll test",
        )

        StudentEnrollment.objects.create(
            student_id=self.student_id,
            course_code=code,
        )

        resp = self._post_add_course(code)

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content.decode("utf-8"))

        self.assertTrue(body.get("success"))
        self.assertEqual(body.get("message"), "already enrolled")

        count = StudentEnrollment.objects.filter(
            student_id=self.student_id,
            course_code=code,
        ).count()
        self.assertEqual(count, 1)
