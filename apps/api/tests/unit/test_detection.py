"""Detection heuristics unit tests (Phase 8) — pure functions, no I/O."""

from __future__ import annotations

from stackup_api.models.enums import DetectionConfidence
from stackup_api.services.detection import scan_file


def test_package_json_detects_known_dependency() -> None:
    content = '{"dependencies": {"stripe": "^14.0.0", "react": "^18.0.0"}}'
    candidates = scan_file("package.json", content)
    assert len(candidates) == 1
    assert candidates[0].vendor_name == "Stripe"
    assert candidates[0].category == "payments"
    assert candidates[0].confidence == DetectionConfidence.high


def test_package_json_detects_scoped_prefix_dependency() -> None:
    content = '{"dependencies": {"@sentry/nextjs": "^8.0.0"}}'
    candidates = scan_file("package.json", content)
    assert len(candidates) == 1
    assert candidates[0].vendor_name == "Sentry"


def test_package_json_ignores_unknown_dependencies() -> None:
    content = '{"dependencies": {"lodash": "^4.0.0"}}'
    assert scan_file("package.json", content) == []


def test_package_json_malformed_returns_no_candidates() -> None:
    assert scan_file("package.json", "{not valid json") == []


def test_requirements_txt_detects_known_package() -> None:
    content = "boto3==1.35.0\nfastapi==0.124\n# a comment\n\nsentry-sdk>=2.0\n"
    candidates = scan_file("requirements.txt", content)
    vendors = {c.vendor_name for c in candidates}
    assert vendors == {"AWS", "Sentry"}


def test_pyproject_toml_detects_referenced_package() -> None:
    content = 'dependencies = [\n  "boto3>=1.35,<2",\n  "fastapi>=0.124,<0.125",\n]\n'
    candidates = scan_file("pyproject.toml", content)
    assert any(c.vendor_name == "AWS" for c in candidates)
    assert all(c.confidence == DetectionConfidence.medium for c in candidates)


def test_render_yaml_presence_is_a_hosting_signal() -> None:
    candidates = scan_file("render.yaml", "services:\n  - type: web\n")
    assert len(candidates) == 1
    assert candidates[0].vendor_name == "Render"
    assert candidates[0].category == "hosting"
    assert candidates[0].confidence == DetectionConfidence.high


def test_vercel_json_presence_is_a_hosting_signal() -> None:
    candidates = scan_file("vercel.json", "{}")
    assert candidates[0].vendor_name == "Vercel"


def test_docker_compose_detects_service_images() -> None:
    content = "services:\n  db:\n    image: postgres:16\n  cache:\n    image: redis:7\n"
    candidates = scan_file("docker-compose.yml", content)
    vendors = {c.vendor_name for c in candidates}
    assert vendors == {"PostgreSQL", "Redis"}


def test_unknown_file_returns_no_candidates() -> None:
    assert scan_file("README.md", "# hello") == []
