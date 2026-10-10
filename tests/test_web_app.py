import io
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen import canvas

import auth_store
from web_app import create_app


class WebsiteFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.store = auth_store.AuthStore(str(root / "accounts.sqlite3"))
        self.app = create_app(self.store, root / "web_jobs")
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def csrf(self):
        with self.client.session_transaction() as session:
            return session["_csrf_token"]

    def create_admin(self):
        self.client.get("/setup")
        response = self.client.post(
            "/setup",
            data={
                "_csrf_token": self.csrf(),
                "username": "admin",
                "password": "long-enough-test-password",
            },
        )
        self.assertEqual(response.status_code, 302)

    @staticmethod
    def sample_pdf():
        stream = io.BytesIO()
        document = canvas.Canvas(stream)
        document.drawString(72, 720, "Website test document")
        document.save()
        stream.seek(0)
        return stream

    def test_setup_login_and_tool_download(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/setup", response.location)
        self.create_admin()

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Find the right tool", response.data)
        icon_response = self.client.get("/brand-icon")
        self.assertEqual(icon_response.status_code, 200)
        icon_response.close()

        response = self.client.post(
            "/api/tools/pdf-information",
            headers={"X-CSRF-Token": self.csrf()},
            data={"file": (self.sample_pdf(), "source.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["result"]["page_count"], 1)
        self.assertNotIn("file_path", response.json["result"])

        response = self.client.post(
            "/api/tools/compress-pdf",
            headers={"X-CSRF-Token": self.csrf()},
            data={
                "file": (self.sample_pdf(), "source.pdf"),
                "level": "low",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200, response.json)
        download = self.client.get(response.json["download_url"])
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.mimetype, "application/pdf")
        download.close()

    def test_admin_invitation_registration_and_account_controls(self):
        self.create_admin()
        csrf = self.csrf()
        invitation_response = self.client.post(
            "/api/admin/invitations",
            headers={"X-CSRF-Token": csrf},
            json={},
        )
        self.assertEqual(invitation_response.status_code, 200)
        invitation = invitation_response.json["invitation"]

        self.client.post("/logout", data={"_csrf_token": csrf})
        self.client.get("/register")
        response = self.client.post(
            "/register",
            data={
                "_csrf_token": self.csrf(),
                "invitation": invitation,
                "username": "member",
                "password": "another-long-test-password",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            self.client.get("/api/admin/users").status_code,
            403,
        )

        self.client.post("/logout", data={"_csrf_token": self.csrf()})
        self.client.get("/login")
        admin_csrf = self.csrf()
        response = self.client.post(
            "/login",
            data={
                "_csrf_token": admin_csrf,
                "username": "admin",
                "password": "long-enough-test-password",
            },
        )
        self.assertEqual(response.status_code, 302)
        admin_csrf = self.csrf()
        response = self.client.post(
            "/api/admin/users/member/password",
            headers={"X-CSRF-Token": admin_csrf},
            json={"password": "reset-long-test-password"},
        )
        self.assertEqual(response.status_code, 200, response.json)
        response = self.client.post(
            "/api/admin/users/member/enabled",
            headers={"X-CSRF-Token": admin_csrf},
            json={"enabled": False},
        )
        self.assertEqual(response.status_code, 200, response.json)
        with self.assertRaises(auth_store.AuthenticationError):
            self.store.authenticate("member", "reset-long-test-password")

    def test_api_rejects_missing_csrf_token(self):
        self.create_admin()
        response = self.client.post("/api/tools/pdf-information")
        self.assertEqual(response.status_code, 400)
        self.assertIn("session expired", response.json["error"].lower())


if __name__ == "__main__":
    unittest.main()
