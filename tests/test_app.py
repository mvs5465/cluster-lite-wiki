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
                "SEED_DIR": data_dir / "missing-seed",
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

    def test_seed_pages_load_when_database_is_empty(self):
        seed_dir = Path(self.temp_dir.name) / "seed-pages"
        seed_dir.mkdir()
        (seed_dir / "cluster.md").write_text(
            "---\n"
            "title: Seed Page\n"
            "slug: seed-page\n"
            "---\n"
            "Seeded content for the cluster wiki.\n",
            encoding="utf-8",
        )

        data_dir = Path(self.temp_dir.name) / "seeded-data"
        app = create_app(
            {
                "TESTING": True,
                "DATA_DIR": data_dir,
                "DATABASE": str(data_dir / "wiki.db"),
                "SEED_DIR": seed_dir,
                "SITE_NAME": "Seeded Wiki",
            }
        )

        response = app.test_client().get("/pages")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Seed Page", response.data)
        self.assertIn(b"Seeded content", response.data)

    def test_seed_does_not_overwrite_existing_pages(self):
        seed_dir = Path(self.temp_dir.name) / "seed-pages"
        seed_dir.mkdir()
        (seed_dir / "cluster.md").write_text(
            "---\n"
            "title: Seed Page\n"
            "slug: seed-page\n"
            "---\n"
            "Original seed body.\n",
            encoding="utf-8",
        )

        data_dir = Path(self.temp_dir.name) / "seeded-data"
        initial_app = create_app(
            {
                "TESTING": True,
                "DATA_DIR": data_dir,
                "DATABASE": str(data_dir / "wiki.db"),
                "SEED_DIR": seed_dir,
                "SITE_NAME": "Seeded Wiki",
            }
        )
        initial_client = initial_app.test_client()
        initial_client.post(
            "/pages",
            data={
                "original_slug": "seed-page",
                "title": "Seed Page",
                "slug": "seed-page",
                "body": "Edited after first boot.",
            },
        )

        restarted_app = create_app(
            {
                "TESTING": True,
                "DATA_DIR": data_dir,
                "DATABASE": str(data_dir / "wiki.db"),
                "SEED_DIR": seed_dir,
                "SITE_NAME": "Seeded Wiki",
            }
        )
        response = restarted_app.test_client().get("/pages/seed-page")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Edited after first boot.", response.data)
        self.assertNotIn(b"Original seed body.", response.data)

    def test_reseed_replaces_existing_pages_with_seed_content(self):
        seed_dir = Path(self.temp_dir.name) / "seed-pages"
        seed_dir.mkdir()
        (seed_dir / "cluster.md").write_text(
            "---\n"
            "title: Seed Page\n"
            "slug: seed-page\n"
            "---\n"
            "Current managed seed body.\n",
            encoding="utf-8",
        )

        data_dir = Path(self.temp_dir.name) / "seeded-data"
        app = create_app(
            {
                "TESTING": True,
                "DATA_DIR": data_dir,
                "DATABASE": str(data_dir / "wiki.db"),
                "SEED_DIR": seed_dir,
                "SITE_NAME": "Seeded Wiki",
            }
        )
        client = app.test_client()
        client.post(
            "/pages",
            data={
                "original_slug": "seed-page",
                "title": "Seed Page",
                "slug": "seed-page",
                "body": "Edited locally.",
            },
        )

        inserted = app.reseed_pages()
        self.assertEqual(inserted, 1)

        response = client.get("/pages/seed-page")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Current managed seed body.", response.data)
        self.assertNotIn(b"Edited locally.", response.data)


if __name__ == "__main__":
    unittest.main()
