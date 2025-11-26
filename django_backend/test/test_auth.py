import json
import bcrypt

from django.test import TestCase
from django.urls import reverse
from stu_accounts.models import StudentAccount


class AuthApiTests(TestCase):

    def setUp(self):
        """Create a valid student account for login tests."""
        self.student_id = "z7654321"
        self.password = "CorrectPassword123!"

        password_hash = bcrypt.hashpw(
            self.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        self.account = StudentAccount.objects.create(
            student_id=self.student_id,
            email="z7654321@unsw.edu.au",
            name="Existing User",
            password_hash=password_hash,
            avatar_url="",
        )

    # ===========================
    # Login API
    # ===========================

    def test_login_success(self):
        """Successful login with correct student_id and password."""
        url = reverse("api_login")
        response = self.client.post(
            url,
            data=json.dumps({"student_id": self.student_id, "password": self.password}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        payload = data["data"]
        self.assertIn("token", payload)
        self.assertIn("user", payload)
        self.assertNotEqual(payload["token"], "")

        # Token should be persisted in the database
        self.account.refresh_from_db()
        self.assertIsNotNone(self.account.current_token)

    def test_login_wrong_password(self):
        """Incorrect password should return 401 with success=False."""
        url = reverse("api_login")
        response = self.client.post(
            url,
            data=json.dumps({"student_id": self.student_id, "password": "WRONG"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid id or password")

    def test_login_missing_fields(self):
        """Missing required fields should return 400."""
        url = reverse("api_login")
        resp = self.client.post(
            url,
            data=json.dumps({"student_id": self.student_id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("id and password are required", resp.json()["message"])

    def test_login_nonexistent_user(self):
        """
        Login attempt with non-existing student_id.
        In the current implementation, this triggers a 500 due to exception during lookup.
        """
        url = reverse("api_login")
        resp = self.client.post(
            url,
            data=json.dumps({"student_id": "z9999999", "password": "AAA"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 500)

    # ===========================
    # Register API
    # ===========================

    def test_register_success(self):
        """Successful registration should return 201."""
        url = reverse("api_register")
        new_user = {
            "student_id": "z1111111",
            "email": "z1111111@unsw.edu.au",
            "name": "NewUser",
            "password": "NewPwd123!"
        }

        response = self.client.post(
            url,
            json.dumps(new_user),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["student_id"], "z1111111")

        # New record should exist in the database
        self.assertTrue(StudentAccount.objects.filter(student_id="z1111111").exists())

    def test_register_duplicate_student_id(self):
        url = reverse("api_register")

        payload = {
            "student_id": self.student_id,  # duplicate
            "email": "another@unsw.edu.au",
            "name": "AnotherUser",
            "password": "ValidPwd123!"   # valid pwd
        }

        resp = self.client.post(url, json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 409)  
        self.assertIn("Student ID already exists", resp.json()["message"])

    def test_register_duplicate_email(self):
        url = reverse("api_register")

        payload = {
            "student_id": "z9999999",
            "email": "z7654321@unsw.edu.au",  # duplicate
            "name": "AnotherUser",
            "password": "ValidPwd123!"
        }

        resp = self.client.post(url, json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 409)
        self.assertIn("Email already exists", resp.json()["message"])

    def test_register_missing_fields(self):
        """Missing required fields should return 400."""
        url = reverse("api_register")
        resp = self.client.post(
            url,
            json.dumps({"student_id": "z1231231"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Please enter zid", resp.json()["message"])

    def test_register_invalid_email(self):
        url = reverse("api_register")

        payload = {
            "student_id": "z7777777",
            "email": "invalid-email",
            "name": "InvalidUser",
            "password": "ValidPwd123!"
        }

        resp = self.client.post(url, json.dumps(payload), content_type="application/json")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("Wrong Email Format", resp.json()["message"])

    def test_register_invalid_password(self):
        """Invalid password format should return 400."""
        url = reverse("api_register")
        payload = {
            "student_id": "z4444444",
            "email": "z4444444@unsw.edu.au",
            "name": "InvalidPwd",
            "password": "123"
        }

        resp = self.client.post(
            url, json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json()["message"])
