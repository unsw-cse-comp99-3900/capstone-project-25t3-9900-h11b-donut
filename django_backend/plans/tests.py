from django.test import TestCase, Client
import base64, json

def make_token(student_id: str) -> str:
    payload = json.dumps({"student_id": student_id}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")

class PlansApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.token = make_token("S1234567")
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_weekly_plan_requires_auth(self):
        resp = self.client.get("/api/plans/weekly/0")
        self.assertEqual(resp.status_code, 401)

    def test_weekly_plan_get_and_put(self):
        # GET：no plan generated
        resp = self.client.get("/api/plans/weekly/0", **self.auth)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("success" in data)

        # PUT：save plan
        payload = {"plan": []}
        resp2 = self.client.put("/api/plans/weekly/0", data=json.dumps(payload), content_type="application/json", **self.auth)
        self.assertEqual(resp2.status_code, 200)