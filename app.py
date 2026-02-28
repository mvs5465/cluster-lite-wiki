import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, abort, g, redirect, render_template, request, url_for
from markupsafe import Markup
import markdown
from opentelemetry import context, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest, multiprocess


SLUG_RE = re.compile(r"[^a-z0-9]+")
WHITESPACE_RE = re.compile(r"\s+")
TRACER_NAME = "cluster-lite-wiki"
_TRACING_CONFIGURED = False
HTTP_REQUESTS = Counter(
    "cluster_lite_wiki_http_requests_total",
    "Total HTTP requests handled by cluster-lite-wiki.",
    ["method", "handler", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "cluster_lite_wiki_http_request_duration_seconds",
    "HTTP request latency for cluster-lite-wiki.",
    ["method", "handler"],
)


def _otlp_endpoint() -> str:
    return (
        os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or ""
    ).strip()


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _otlp_insecure(endpoint: str) -> bool:
    if not endpoint:
        return False
    if "OTEL_EXPORTER_OTLP_TRACES_INSECURE" in os.environ:
        return _env_flag("OTEL_EXPORTER_OTLP_TRACES_INSECURE", False)
    if "OTEL_EXPORTER_OTLP_INSECURE" in os.environ:
        return _env_flag("OTEL_EXPORTER_OTLP_INSECURE", False)
    return endpoint.startswith("http://")


def configure_tracing() -> bool:
    global _TRACING_CONFIGURED

    endpoint = _otlp_endpoint()
    if not endpoint:
        return False
    if _TRACING_CONFIGURED:
        return True

    provider = TracerProvider(
        resource=Resource.create(
            {"service.name": os.environ.get("OTEL_SERVICE_NAME", TRACER_NAME)}
        )
    )
    exporter = OTLPSpanExporter(
        endpoint=endpoint,
        insecure=_otlp_insecure(endpoint),
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True
    return True


def _start_request_span() -> None:
    tracer = trace.get_tracer(TRACER_NAME)
    span = tracer.start_span(
        f"{request.method} {request.path}",
        kind=SpanKind.SERVER,
    )
    span.set_attribute("http.request.method", request.method)
    span.set_attribute("url.path", request.path)
    if request.host:
        span.set_attribute("server.address", request.host)

    token = context.attach(trace.set_span_in_context(span))
    g._otel_request_span = span
    g._otel_request_token = token


def _finish_request_span(*, status_code: int | None = None, error_obj: BaseException | None = None) -> None:
    span = g.pop("_otel_request_span", None)
    token = g.pop("_otel_request_token", None)
    if span is None:
        return

    if status_code is not None:
        span.set_attribute("http.response.status_code", status_code)
        if status_code >= 500:
            span.set_status(Status(StatusCode.ERROR))

    if error_obj is not None:
        span.record_exception(error_obj)
        span.set_status(Status(StatusCode.ERROR))

    span.end()
    if token is not None:
        context.detach(token)


def _handler_label() -> str:
    if request.url_rule is not None:
        return request.url_rule.rule
    return request.path


def _metrics_response() -> Response:
    multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "").strip()
    if multiproc_dir:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        payload = generate_latest(registry)
    else:
        payload = generate_latest()
    return Response(payload, mimetype=CONTENT_TYPE_LATEST)


def _normalize_sql(statement: str) -> str:
    return " ".join(statement.split())


def execute_sql(db: sqlite3.Connection, statement: str, parameters=()):
    tracer = trace.get_tracer(TRACER_NAME)
    normalized = _normalize_sql(statement)
    with tracer.start_as_current_span("sqlite.query", kind=SpanKind.CLIENT) as span:
        span.set_attribute("db.system", "sqlite")
        span.set_attribute("db.operation.name", normalized.split(" ", 1)[0].upper())
        span.set_attribute("db.query.text", normalized)
        return db.execute(statement, parameters)


def execute_many_sql(db: sqlite3.Connection, statement: str, parameters):
    tracer = trace.get_tracer(TRACER_NAME)
    normalized = _normalize_sql(statement)
    with tracer.start_as_current_span("sqlite.query", kind=SpanKind.CLIENT) as span:
        span.set_attribute("db.system", "sqlite")
        span.set_attribute("db.operation.name", normalized.split(" ", 1)[0].upper())
        span.set_attribute("db.query.text", normalized)
        return db.executemany(statement, parameters)


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


def build_excerpt(source: str, limit: int = 260) -> str:
    text = re.sub(r"```.*?```", " ", source, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = text.replace("|", " ")
    text = WHITESPACE_RE.sub(" ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def categorize_page(page: sqlite3.Row) -> str:
    text = f"{page['title']} {page['slug']}".lower()

    if any(term in text for term in ("overview", "catalog", "access", "ingress")):
        return "Core Docs"
    if any(term in text for term in ("ai", "query", "gitops", "repo", "platform", "mcp")):
        return "Platform"
    if any(term in text for term in ("observability", "debug", "storage", "runbook")):
        return "Operations"
    return "General"


def group_pages(pages) -> list[tuple[str, list[sqlite3.Row]]]:
    order = ["Core Docs", "Operations", "Platform", "General"]
    grouped: dict[str, list[sqlite3.Row]] = {name: [] for name in order}

    for page in pages:
        grouped[categorize_page(page)].append(page)

    return [
        (name, grouped[name])
        for name in order
        if grouped[name]
    ]


def choose_featured_page(pages):
    if not pages:
        return None

    preferred_slugs = [
        "cluster-overview",
        "service-catalog",
        "access-and-ingress",
    ]
    for slug in preferred_slugs:
        for page in pages:
            if page["slug"] == slug:
                return page
    return pages[0]


def parse_seed_page(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = raw

    if raw.startswith("---\n"):
        marker = "\n---\n"
        end_index = raw.find(marker, 4)
        if end_index != -1:
            header = raw[4:end_index]
            body = raw[end_index + len(marker):]
            for line in header.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                key, separator, value = stripped.partition(":")
                if not separator:
                    raise ValueError(f"Invalid seed metadata line in {path.name}: {line}")
                metadata[key.strip()] = value.strip()

    title = metadata.get("title", "").strip()
    if not title:
        raise ValueError(f"Seed page {path.name} is missing a title")

    content = body.strip()
    if not content:
        raise ValueError(f"Seed page {path.name} has no body content")

    return {
        "slug": slugify(metadata.get("slug", title)),
        "title": title,
        "body": content,
    }


def load_seed_pages(seed_dir: Path) -> list[dict[str, str]]:
    if not seed_dir.exists():
        return []

    pages: list[dict[str, str]] = []
    for path in sorted(seed_dir.glob("*.md")):
        pages.append(parse_seed_page(path))
    return pages


def write_seed_pages(
    db: sqlite3.Connection,
    seed_pages: list[dict[str, str]],
    *,
    replace_existing: bool = False,
) -> int:
    if replace_existing:
        execute_sql(db, "DELETE FROM pages")

    if not seed_pages:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    execute_many_sql(
        db,
        """
        INSERT INTO pages (slug, title, body, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                page["slug"],
                page["title"],
                page["body"],
                now,
                now,
            )
            for page in seed_pages
        ],
    )
    return len(seed_pages)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    tracing_enabled = configure_tracing()
    app_root = Path(__file__).resolve().parent

    data_dir = Path(
        (test_config or {}).get("DATA_DIR")
        or os.environ.get("WIKI_DATA_DIR")
        or (Path.cwd() / "data")
    )
    seed_dir = Path(
        (test_config or {}).get("SEED_DIR")
        or os.environ.get("WIKI_SEED_DIR")
        or (app_root / "seed" / "pages")
    )
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "wiki.db"

    app.config.update(
        DATA_DIR=data_dir,
        DATABASE=str(db_path),
        SEED_DIR=seed_dir,
        SITE_NAME=os.environ.get("WIKI_SITE_NAME", "Cluster Lite Wiki"),
    )

    if test_config:
        app.config.update(test_config)

    if tracing_enabled:
        @app.before_request
        def begin_request_span() -> None:
            _start_request_span()

        @app.after_request
        def end_request_span(response):
            _finish_request_span(status_code=response.status_code)
            return response

        @app.teardown_request
        def teardown_request_span(error_obj: BaseException | None) -> None:
            if error_obj is not None:
                _finish_request_span(error_obj=error_obj)

    @app.before_request
    def begin_metrics_timer() -> None:
        if request.path == "/metrics":
            return
        g._metrics_started_at = time.perf_counter()

    @app.after_request
    def record_request_metrics(response):
        started_at = g.pop("_metrics_started_at", None)
        if started_at is None:
            return response

        handler = _handler_label()
        duration = max(time.perf_counter() - started_at, 0.0)
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            handler=handler,
        ).observe(duration)
        HTTP_REQUESTS.labels(
            method=request.method,
            handler=handler,
            status=str(response.status_code),
        ).inc()
        return response

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    def init_db() -> None:
        db = sqlite3.connect(app.config["DATABASE"])
        execute_sql(
            db,
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

        existing_rows = execute_sql(db, "SELECT COUNT(*) FROM pages").fetchone()[0]
        if existing_rows == 0:
            seed_pages = load_seed_pages(app.config["SEED_DIR"])
            if write_seed_pages(db, seed_pages) > 0:
                db.commit()
        db.close()

    def reseed_pages() -> int:
        db = sqlite3.connect(app.config["DATABASE"])
        try:
            execute_sql(
                db,
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
            seed_pages = load_seed_pages(app.config["SEED_DIR"])
            inserted = write_seed_pages(db, seed_pages, replace_existing=True)
            db.commit()
            return inserted
        finally:
            db.close()

    @app.teardown_appcontext
    def close_db(_error: BaseException | None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.template_filter("markdown")
    def markdown_filter(value: str) -> Markup:
        return render_markdown(value)

    @app.template_filter("excerpt")
    def excerpt_filter(value: str, limit: int = 260) -> str:
        return build_excerpt(value, limit)

    @app.context_processor
    def inject_globals() -> dict:
        return {"site_name": app.config["SITE_NAME"]}

    @app.get("/")
    def index():
        return redirect(url_for("list_pages"))

    @app.get("/metrics")
    def metrics():
        return _metrics_response()

    @app.get("/pages")
    def list_pages():
        query = request.args.get("q", "").strip()
        db = get_db()
        if query:
            like = f"%{query}%"
            pages = execute_sql(
                db,
                """
                SELECT slug, title, body, updated_at
                FROM pages
                WHERE title LIKE ? OR body LIKE ?
                ORDER BY title COLLATE NOCASE
                """,
                (like, like),
            ).fetchall()
        else:
            pages = execute_sql(
                db,
                """
                SELECT slug, title, body, updated_at
                FROM pages
                ORDER BY title COLLATE NOCASE
                """
            ).fetchall()
        return render_template(
            "list.html",
            pages=pages,
            featured_page=choose_featured_page(pages),
            grouped_pages=group_pages(pages),
            query=query,
        )

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
                page = execute_sql(
                    db,
                    "SELECT id FROM pages WHERE slug = ?",
                    (original_slug,),
                ).fetchone()
                if page is None:
                    abort(404)
                execute_sql(
                    db,
                    """
                    UPDATE pages
                    SET slug = ?, title = ?, body = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (slug, title, body, now, page["id"]),
                )
            else:
                execute_sql(
                    db,
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
        db = get_db()
        page = execute_sql(
            db,
            """
            SELECT slug, title, body, created_at, updated_at
            FROM pages
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
        if page is None:
            abort(404)
        nav_pages = execute_sql(
            db,
            """
            SELECT slug, title, body, updated_at
            FROM pages
            ORDER BY title COLLATE NOCASE
            """
        ).fetchall()
        return render_template(
            "view.html",
            page=page,
            nav_pages=nav_pages,
            grouped_pages=group_pages(nav_pages),
        )

    @app.get("/pages/<slug>/edit")
    def edit_page(slug: str):
        page = execute_sql(
            get_db(),
            "SELECT slug, title, body FROM pages WHERE slug = ?",
            (slug,),
        ).fetchone()
        if page is None:
            abort(404)
        return render_template("edit.html", page=page, is_new=False)

    app.reseed_pages = reseed_pages
    init_db()
    return app


if __name__ == "__main__":
    app = create_app()
    if len(sys.argv) > 1 and sys.argv[1] == "reseed":
        inserted = app.reseed_pages()
        print(
            f"Replaced wiki contents with {inserted} seed page"
            f"{'' if inserted == 1 else 's'}."
        )
        raise SystemExit(0)
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
