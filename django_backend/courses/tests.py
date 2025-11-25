from django.test import TestCase, Client
from django.urls import reverse
import base64, json

def make_token(student_id: str) -> str:
    payload = json.dumps({"student_id": student_id}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")

class CoursesApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.token = make_token("S1234567")
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_available_courses_requires_auth(self):
        resp = self.client.get("/api/courses/available")
        self.assertEqual(resp.status_code, 401)

    def test_available_courses_ok(self):
        resp = self.client.get("/api/courses/available", **self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)
        self.assertGreater(len(data.get("data")), 0)

    def test_materials_and_download(self):
  
        resp = self.client.get("/api/courses/COMP9900/materials", **self.auth)
        self.assertEqual(resp.status_code, 200)
        mats = resp.json().get("data") or []
        self.assertTrue(isinstance(mats, list))
        
        resp2 = self.client.get("/api/materials/comp9900-coach-pdf/download", **self.auth)
       
        self.assertIn(resp2.status_code, (200, 404))