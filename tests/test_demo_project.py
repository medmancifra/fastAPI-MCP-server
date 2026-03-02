"""Tests for demo_project assets and the smoke/serve entrypoint contract."""

import os
import subprocess
from pathlib import Path

from PIL import Image

DEMO_DIR = Path(__file__).parent.parent / "demo_project"
IMAGES_DIR = DEMO_DIR / "images"


class TestDemoProjectAssets:
    """Verify that required demo assets exist and are valid images."""

    def test_ocr_sample_exists(self):
        assert (IMAGES_DIR / "ocr_sample.png").is_file(), (
            "demo_project/images/ocr_sample.png must exist"
        )

    def test_barcode_qr_sample_exists(self):
        assert (IMAGES_DIR / "barcode_qr_sample.png").is_file(), (
            "demo_project/images/barcode_qr_sample.png must exist"
        )

    def test_ocr_sample_is_valid_image(self):
        img = Image.open(IMAGES_DIR / "ocr_sample.png")
        assert img.width > 0 and img.height > 0
        assert img.format == "PNG"

    def test_barcode_qr_sample_is_valid_image(self):
        img = Image.open(IMAGES_DIR / "barcode_qr_sample.png")
        assert img.width > 0 and img.height > 0
        assert img.format == "PNG"

    def test_demo_dir_total_size_under_10mb(self):
        """demo_project/ must stay under 10 MB as required by the issue."""
        total = sum(f.stat().st_size for f in DEMO_DIR.rglob("*") if f.is_file())
        limit = 10 * 1024 * 1024  # 10 MB
        assert total < limit, (
            f"demo_project/ is {total / 1024 / 1024:.2f} MB, must be < 10 MB"
        )


class TestEntrypointScript:
    """Verify the entrypoint.sh script exists and handles unknown commands correctly."""

    ENTRYPOINT = Path(__file__).parent.parent / "entrypoint.sh"

    def test_entrypoint_exists(self):
        assert self.ENTRYPOINT.is_file(), "entrypoint.sh must exist at repo root"

    def test_entrypoint_is_executable(self):
        assert os.access(self.ENTRYPOINT, os.X_OK), "entrypoint.sh must be executable"

    def test_unknown_command_exits_nonzero(self):
        result = subprocess.run(
            [str(self.ENTRYPOINT), "unknown-command"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "entrypoint.sh should exit with non-zero code for unknown commands"
        )
        assert "ERROR" in result.stdout or "ERROR" in result.stderr


class TestEnvExample:
    """Verify .env.example exists and contains required variable names."""

    ENV_EXAMPLE = Path(__file__).parent.parent / ".env.example"

    def test_env_example_exists(self):
        assert self.ENV_EXAMPLE.is_file(), ".env.example must exist at repo root"

    def test_env_example_has_descope_project_id(self):
        content = self.ENV_EXAMPLE.read_text()
        assert "DESCOPE_PROJECT_ID" in content

    def test_env_example_has_descope_api_base_url(self):
        content = self.ENV_EXAMPLE.read_text()
        assert "DESCOPE_API_BASE_URL" in content

    def test_env_example_has_no_real_secrets(self):
        """Ensure .env.example only contains placeholder values, not real tokens."""
        content = self.ENV_EXAMPLE.read_text()
        # A real Descope project ID starts with 'P' followed by ~27 chars
        # Placeholder values should contain '<' or 'your' or be absent
        lines = [
            line for line in content.splitlines()
            if line.startswith("DESCOPE_PROJECT_ID=") and not line.strip().endswith("=")
        ]
        for line in lines:
            value = line.split("=", 1)[1].strip()
            assert "<" in value or "your" in value.lower(), (
                f"DESCOPE_PROJECT_ID in .env.example looks like a real secret: {value}"
            )
