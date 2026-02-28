import tempfile
import unittest
from pathlib import Path

from app import create_app


class WikiAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        data_dir = Path(self.temp_dir.name)
        self.app = create_app(
            {
                "TESTING": True,
                "DATA_DIR": data_dir,
                "DATABASE": str(data_dir / "wiki.db"),
                "SITE_NAME": "Test Wiki",
            }
        )
        self.client = self.app.test_client()

    def test_create_and_edit_page(self):
        create_response = self.client.post(
            "/pages",
            data={
                "title": "Runbook",
                "body": "# Welcome\n\nInitial content.",
            },
            follow_redirects=False,
        )
        self.assertEqual(create_response.status_code, 302)
        self.assertIn("/pages/runbook", create_response.headers["Location"])

        view_response = self.client.get("/pages/runbook")
        self.assertEqual(view_response.status_code, 200)
        self.assertIn(b"Runbook", view_response.data)
        self.assertIn(b"Welcome", view_response.data)

        edit_response = self.client.post(
            "/pages",
            data={
                "original_slug": "runbook",
                "slug": "ops-runbook",
                "title": "Ops Runbook",
                "body": "Updated body.",
            },
            follow_redirects=False,
        )
        self.assertEqual(edit_response.status_code, 302)
        self.assertIn("/pages/ops-runbook", edit_response.headers["Location"])

        updated_view = self.client.get("/pages/ops-runbook")
        self.assertEqual(updated_view.status_code, 200)
        self.assertIn(b"Ops Runbook", updated_view.data)
        self.assertIn(b"Updated body.", updated_view.data)

    def test_search_filters_pages(self):
        self.client.post(
            "/pages",
            data={"title": "Alpha", "body": "cluster setup notes"},
        )
        self.client.post(
            "/pages",
            data={"title": "Beta", "body": "random topic"},
        )

        response = self.client.get("/pages?q=setup")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alpha", response.data)
        self.assertNotIn(b"Beta", response.data)


if __name__ == "__main__":
    unittest.main()
