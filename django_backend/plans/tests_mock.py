from django.test import TestCase, Client
from datetime import datetime, timedelta
import base64, json

from courses.views import MY_COURSES_BY_STUDENT, TASKS_BY_COURSE

def make_token(student_id: str) -> str:
    """Generate a simple Base64 Token that is consistent with utilits.auth.make_token"""
    payload = json.dumps({"student_id": student_id}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")

class PlansAndTasksMockTests(TestCase):
    """
    Using pure memory to simulate data testing:
-Does the/app/courses/{id}/tasks interface return tasks (with courseId)
-Does/app/plans/weekly/{offset} return generated parts (with complete fields)
    """

    def setUp(self):
        self.client = Client()
        self.sid = "S1234567"
        self.token = make_token(self.sid)
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}


        MY_COURSES_BY_STUDENT[self.sid] = ["COMP9900"]

        TASKS_BY_COURSE["COMP9900"] = [
            {
                "id": "1",
                "title": "Mock Proposal",
                "deadline": "2025-12-31",
                "brief": "Write a short proposal",
                "percentContribution": 30,
            },
            {
                "id": "2",
                "title": "Mock Report",
                "deadline": "2025-11-20",
                "brief": "Mid-term progress report",
                "percentContribution": 70,
            },
        ]

    def test_tasks_endpoint_returns_course_tasks(self):
      
        resp = self.client.get("/api/courses/COMP9900/tasks", **self.auth)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"), f"payload={payload}")
        tasks = payload.get("data") or []
        self.assertGreater(len(tasks), 0, "task list cannot be empty")


        first = tasks[0]
        for key in ("id", "title", "deadline", "brief", "percentContribution", "courseId"):
            self.assertIn(key, first, f"missing: {key}")

  
        self.assertEqual(first["courseId"], "COMP9900")

    def test_weekly_plan_returns_parts(self):

        resp = self.client.get("/api/plans/weekly/0", **self.auth)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"), f"payload={payload}")
        items = payload.get("data") or []
        self.assertGreater(len(items), 0, "task list cannot be empty")

      
        required_keys = [
            "id", "courseId", "courseTitle", "partTitle",
            "minutes", "date", "color", "completed",
            "partIndex", "partsCount",
        ]
        for it in items:
            for k in required_keys:
                self.assertIn(k, it, f"missing: {k} -> {it}")

        now = datetime.now()
        monday = now - timedelta(days=now.weekday())  # Monday=0
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

        def parse_date(dstr: str) -> datetime:
            return datetime.strptime(dstr, "%Y-%m-%d")

        for it in items[:7]:  
            d = parse_date(it["date"])
            self.assertTrue(monday <= d <= sunday, f"date should between: {it['date']}")



    def test_material_download_status(self):

        resp = self.client.get("/api/materials/comp9900-coach-pdf/download", **self.auth)
        self.assertIn(resp.status_code, (200, 404), f"unexpected status: {resp.status_code}")