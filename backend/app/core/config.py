"""Application configuration.

All configuration is sourced from environment variables (Blueprint Vol. 04:
"No secrets in code; use environment configuration"). Values are read once at
import time into a cached ``Settings`` instance.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, loaded from the environment (prefix ``WES_``)."""

    model_config = SettingsConfigDict(
        env_prefix="WES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WES Company Engine"
    env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Runtime initialization. When auto_migrate is on, the backend applies Alembic
    # migrations on startup against the database it will serve, so the schema is
    # always present (no "no such table" errors). seed_on_start loads the initial
    # WES organization (idempotent).
    auto_migrate: bool = True
    seed_on_start: bool = True

    # SQLite default keeps local dev and tests zero-dependency; production uses
    # PostgreSQL via WES_DATABASE_URL (see .env.example / docker-compose).
    database_url: str = "sqlite:///./wes_os.db"

    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    # --- Authentication / JWT (Sprint 04) ---
    # WES_JWT_SECRET MUST be overridden in production. The default is for local
    # development only.
    jwt_secret: str = "dev-insecure-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    refresh_token_remember_days: int = 30
    # Default password applied to seeded employees so they can log in locally.
    seed_default_password: str = "WesOs2026!"

    # --- Provider Platform / secret management (Sprint 11) ---
    # WES_SECRET_KEY encrypts provider credentials at rest. MUST be overridden in
    # production. A per-install random key would rotate ciphertext on restart, so a
    # stable default is used for local dev only.
    secret_key: str = "dev-insecure-secret-key-change-in-production"
    # Active environment profile — provider secrets are scoped to a profile so the
    # same install can hold development / staging / production credentials.
    active_environment: str = "development"
    # Default HTTP timeout (seconds) for live provider API calls.
    provider_http_timeout: float = 60.0

    # --- Execution→PR Bridge (F10 design; decisions A1-a/A2-a/A3-a/A4) -----
    # A4: author mailbox pattern for AI-authored commits ({employee} slug) and
    # the mechanical committer identity. Configuration, never hard-coded.
    bridge_author_mailbox_pattern: str = "bots+wes-{employee}@wes.studio"
    bridge_committer_name: str = "wes-oi-app[bot]"
    bridge_committer_email: str = "wes-oi-app[bot]@users.noreply.github.com"
    # §C-2 rule 1: the live working tree the bridge must never touch.
    bridge_live_tree_guard: str = "/opt/wes-green"
    # A3-a gate floor (mirrors WES-DEC-004).
    bridge_coverage_floor: int = 71
    # F17: the app root under the clone root. WES nests the app under ``backend/``;
    # other repos may differ, so this is configuration, never hard-coded. Artifact
    # paths (``app/core/...``, ``tests/...``) are written under, and the gate runs
    # in, ``<clone>/<bridge_repo_subdir>``. Empty string => the clone root is the app root.
    bridge_repo_subdir: str = "backend"

    # --- Autonomous Development Engine (Sprint 13) ---
    # Base directory for per-task git sandboxes. Every autonomous implementation
    # runs in a real, isolated git repository UNDER this path — never the WES,
    # WORLD, or Blueprint repositories. Defaults to a temp location.
    dev_workspace_dir: str = "/tmp/wes-dev-workspaces"

    # --- GitHub remote (Blueprint Vol 04 Git Workflow / Vol 06 source of truth) ---
    # GitHub is the Blueprint's declared source of truth, so delivered work must
    # leave the sandbox. Transport is an SSH deploy key: the private key never
    # enters the repository or the database, only this path. All three are empty
    # by default, which disables remote operations entirely (offline test suite
    # and existing behaviour are unchanged).
    github_ssh_url: str = ""
    github_deploy_key_path: str = ""
    github_default_branch: str = "main"

    # --- GitHub App (P0-B — REST API auth: PRs, merge, repo bootstrap) ---
    # Authentication is a GitHub App: a short-lived RS256 JWT is exchanged for an
    # installation access token (auto-refreshed before expiry). The private key
    # lives only at this path — never in the repository, never in the database,
    # never logged. Empty by default → the REST layer is disabled and behaviour
    # is unchanged. ``github_repo`` is "owner/name".
    github_app_id: str = ""
    github_app_installation_id: str = ""
    github_app_private_key_path: str = ""
    github_app_client_id: str = ""
    github_repo: str = ""
    # Optional: deliver PRs into this base branch instead of the default branch.
    # Lets a demonstration target a throwaway base so the real default branch is
    # never touched. Empty → delivery uses ``github_default_branch``.
    github_delivery_base: str = ""

    # Durable background job worker (WP3). Off by default so the synchronous test
    # suite and existing behavior are unchanged; enable in a real deployment.
    job_worker_enabled: bool = False

    # --- Security hardening (WP5) ---
    # Rate limiting is off by default so the test suite is unaffected; enable it in
    # a real deployment via WES_RATE_LIMIT_ENABLED=true. Limits are per client-IP
    # per rolling 60s window.
    rate_limit_enabled: bool = False
    rate_limit_default: int = 300  # general endpoints
    rate_limit_auth: int = 10  # /auth/login and friends (anti brute-force)

    # Root of the WES monorepo — used by the autonomous workflow's intent resolver
    # to discover existing source files (e.g. frontend/src/pages/Dashboard.tsx) when
    # a task is about modifying, not scaffolding. Defaults to the repo root computed
    # from this file's location (backend/app/core/config.py -> parents[3]).
    project_root: str = str(__import__("pathlib").Path(__file__).resolve().parents[3])

    # --- Enterprise DevOps Platform (Sprint 15) ---
    # Base directory for build artifacts and local (real) deployments — never a
    # real production host. Deployments extract the built artifact and verify it.
    devops_workspace_dir: str = "/tmp/wes-devops"
    # Whether the CI/CD pipeline runs REAL `docker build` steps (requires a Docker
    # daemon). Off by default so the test suite stays fast; enabled in runtime.
    devops_docker_builds: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
