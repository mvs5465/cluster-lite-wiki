import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, url_for
from markupsafe import Markup
import markdown


SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.strip().lower()).strip("-")
    if not slug:
        raise ValueError("Slug cannot be empty")
    return slug


def render_markdown(source: str) -> Markup:
    html = markdown.markdown(
        source,
        extensions=["extra", "sane_lists", "tables"],
        output_format="html5",
    )
    return Markup(html)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    data_dir = Path(
        (test_config or {}).get("DATA_DIR")
        or os.environ.get("WIKI_DATA_DIR")
        or (Path.cwd() / "data")
    )
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "wiki.db"

    app.config.update(
        DATA_DIR=data_dir,
        DATABASE=str(db_path),
        SITE_NAME=os.environ.get("WIKI_SITE_NAME", "Cluster Lite Wiki"),
    )

    if test_config:
        app.config.update(test_config)

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    def init_db() -> None:
        db = sqlite3.connect(app.config["DATABASE"])
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        db.commit()
        db.close()

    @app.teardown_appcontext
    def close_db(_error: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.template_filter("markdown")
    def markdown_filter(value: str) -> Markup:
        return render_markdown(value)

    @app.context_processor
    def inject_globals() -> dict:
        return {"site_name": app.config["SITE_NAME"]}

    @app.get("/")
    def index():
        return redirect(url_for("list_pages"))

    @app.get("/pages")
    def list_pages():
        query = request.args.get("q", "").strip()
        db = get_db()
        if query:
            like = f"%{query}%"
            pages = db.execute(
                """
                SELECT slug, title, body, updated_at
                FROM pages
                WHERE title LIKE ? OR body LIKE ?
                ORDER BY title COLLATE NOCASE
                """,
                (like, like),
            ).fetchall()
        else:
            pages = db.execute(
                """
                SELECT slug, title, body, updated_at
                FROM pages
                ORDER BY title COLLATE NOCASE
                """
            ).fetchall()
        return render_template("list.html", pages=pages, query=query)

    @app.get("/pages/new")
    def new_page():
        return render_template(
            "edit.html",
            page={"slug": "", "title": "", "body": ""},
            is_new=True,
        )

    @app.post("/pages")
    def save_page():
        db = get_db()
        original_slug = request.form.get("original_slug", "").strip()
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        requested_slug = request.form.get("slug", "").strip()

        if not title:
            abort(400, "Title is required")
        if not body:
            abort(400, "Body is required")

        try:
            slug = slugify(requested_slug or title)
        except ValueError as exc:
            abort(400, str(exc))

        now = datetime.now(timezone.utc).isoformat()

        try:
            if original_slug:
                page = db.execute(
                    "SELECT id FROM pages WHERE slug = ?",
                    (original_slug,),
                ).fetchone()
                if page is None:
                    abort(404)
                db.execute(
                    """
                    UPDATE pages
                    SET slug = ?, title = ?, body = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (slug, title, body, now, page["id"]),
                )
            else:
                db.execute(
                    """
                    INSERT INTO pages (slug, title, body, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (slug, title, body, now, now),
                )
        except sqlite3.IntegrityError:
            abort(409, "A page with that slug already exists")

        db.commit()
        return redirect(url_for("view_page", slug=slug))

    @app.get("/pages/<slug>")
    def view_page(slug: str):
        page = get_db().execute(
            """
            SELECT slug, title, body, created_at, updated_at
            FROM pages
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
        if page is None:
            abort(404)
        return render_template("view.html", page=page)

    @app.get("/pages/<slug>/edit")
    def edit_page(slug: str):
        page = get_db().execute(
            "SELECT slug, title, body FROM pages WHERE slug = ?",
            (slug,),
        ).fetchone()
        if page is None:
            abort(404)
        return render_template("edit.html", page=page, is_new=False)

    init_db()
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
