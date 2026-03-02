"""Tests for demo_project scripts and refactored app modules."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add demo_project to path so we can import demo modules directly
DEMO_DIR = Path(__file__).parent.parent / "demo_project"
sys.path.insert(0, str(DEMO_DIR))


# =============================================================================
# Tests for demo1.py
# =============================================================================

class TestDemo1:
    """Tests for the health-check / tool-listing demo."""

    def test_check_health_success(self):
        import demo1
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "healthy",
            "mcp_tools": ["optical-character-recognition", "scan-barcode"],
        }
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            data = demo1.check_health("http://localhost:8000")
        assert data["status"] == "healthy"
        assert "optical-character-recognition" in data["mcp_tools"]

    def test_main_returns_0_when_healthy(self):
        import demo1
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "healthy",
            "mcp_tools": ["optical-character-recognition", "scan-barcode"],
        }
        mock_resp.raise_for_status = MagicMock()
        with (
            patch("requests.get", return_value=mock_resp),
            patch("sys.argv", ["demo1.py", "--host", "localhost", "--port", "8000"]),
        ):
            code = demo1.main()
        assert code == 0

    def test_main_returns_1_on_connection_error(self):
        import demo1
        import requests as req
        with (
            patch("requests.get", side_effect=req.ConnectionError("down")),
            patch("sys.argv", ["demo1.py"]),
        ):
            code = demo1.main()
        assert code == 1

    def test_main_returns_1_when_unhealthy(self):
        import demo1
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "degraded", "mcp_tools": []}
        mock_resp.raise_for_status = MagicMock()
        with (
            patch("requests.get", return_value=mock_resp),
            patch("sys.argv", ["demo1.py"]),
        ):
            code = demo1.main()
        assert code == 1


# =============================================================================
# Tests for demo4.py (scikit-learn, no server needed — local fallback)
# =============================================================================

class TestDemo4LocalFallback:
    """Tests for the scikit-learn demo using the local fallback analyzer."""

    def test_local_extract_features_simple_code(self):
        import demo4
        features = demo4._local_extract_features("x = 1\n")
        assert len(features) == 5
        loc, funcs, classes, imports, complexity = features
        assert loc >= 1
        assert funcs == 0
        assert classes == 0
        assert imports == 0
        assert 1 <= complexity <= 10

    def test_local_extract_features_complex_code(self):
        import demo4
        code = (
            "import os\nimport sys\n"
            "class Foo:\n    def bar(self):\n"
            "        for i in range(10):\n"
            "            if i > 5:\n                pass\n"
        )
        features = demo4._local_extract_features(code)
        loc, funcs, classes, imports, complexity = features
        assert funcs >= 1
        assert classes >= 1
        assert imports >= 2

    def test_local_extract_features_syntax_error(self):
        import demo4
        # Should not raise; falls back to regex
        features = demo4._local_extract_features("def (broken syntax")
        assert len(features) == 5

    def test_mcp_feature_extractor_falls_back_to_local(self):
        """When the MCP server is unreachable, the extractor uses local analysis."""
        import demo4
        extractor = demo4.MCPCodeFeatureExtractor(
            mcp_base_url="http://127.0.0.1:19999",  # unreachable
            token="",
        )
        X = ["def foo(): pass\n", "x = 1\n"]
        result = extractor.transform(X)
        assert result.shape == (2, 5)
        assert extractor._use_local is True

    def test_parse_mcp_response(self):
        import demo4
        text = (
            "## Code Analysis Results\n\nMetrics:\n"
            "- Lines of Code: 42\n"
            "- Functions: 3\n"
            "- Classes: 1\n"
            "- Imports: 5\n"
            "- Cyclomatic Complexity: 4/10\n"
        )
        features = demo4._parse_mcp_response(text)
        assert features == [42.0, 3.0, 1.0, 5.0, 4.0]

    def test_full_pipeline_runs(self):
        """End-to-end: train + predict on the built-in corpus."""
        import demo4
        import warnings
        warnings.filterwarnings("ignore")

        from sklearn.ensemble import RandomForestClassifier
        from sklearn.pipeline import Pipeline

        pipeline = Pipeline([
            ("features", demo4.MCPCodeFeatureExtractor(
                mcp_base_url="http://127.0.0.1:19999",  # unreachable → local fallback
            )),
            ("clf", RandomForestClassifier(n_estimators=10, random_state=0)),
        ])
        codes = [c for c, _ in demo4.CORPUS]
        labels = [lbl for _, lbl in demo4.CORPUS]
        pipeline.fit(codes, labels)
        predictions = pipeline.predict(codes)
        assert len(predictions) == len(labels)
        assert set(predictions).issubset({"simple", "complex"})


# =============================================================================
# Tests for demo5.py (AI agent bot intent classification)
# =============================================================================

class TestDemo5IntentClassifier:
    """Tests for the agent's intent classification logic."""

    def test_ocr_intent(self):
        import demo5
        assert demo5.classify_intent("read text from https://example.com/a.png") == "ocr"
        assert demo5.classify_intent("extract text from this image") == "ocr"

    def test_barcode_intent(self):
        import demo5
        assert demo5.classify_intent("scan barcode https://example.com/qr.png") == "barcode"
        assert demo5.classify_intent("decode qr code at https://foo.com/img.png") == "barcode"

    def test_health_intent(self):
        import demo5
        assert demo5.classify_intent("check health") == "health"
        assert demo5.classify_intent("status please") == "health"

    def test_help_intent(self):
        import demo5
        assert demo5.classify_intent("help") == "help"
        assert demo5.classify_intent("?") == "help"

    def test_exit_intent(self):
        import demo5
        assert demo5.classify_intent("exit") == "exit"
        assert demo5.classify_intent("quit") == "exit"
        assert demo5.classify_intent("bye") == "exit"

    def test_unknown_intent(self):
        import demo5
        assert demo5.classify_intent("hello world") == "unknown"

    def test_url_fallback_to_ocr(self):
        import demo5
        # A URL with no keyword defaults to OCR
        assert demo5.classify_intent("https://example.com/photo.png") == "ocr"

    def test_extract_url(self):
        import demo5
        url = demo5.extract_url("read text from https://example.com/img.png")
        assert url == "https://example.com/img.png"

    def test_extract_url_none(self):
        import demo5
        assert demo5.extract_url("no url here") is None

    def test_call_ocr_success(self):
        import demo5
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"text": "Hello World"}
        with patch("requests.post", return_value=mock_resp):
            result = demo5.call_ocr("http://localhost:8000", "https://x.com/a.png", "tok")
        assert "Hello World" in result

    def test_call_barcode_success(self):
        import demo5
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "barcodes": [{"type": "QRCODE", "data": "https://github.com", "bounds": {}}],
        }
        with patch("requests.post", return_value=mock_resp):
            result = demo5.call_barcode("http://localhost:8000", "https://x.com/qr.png", "")
        assert "QRCODE" in result
        assert "https://github.com" in result

    def test_call_health_success(self):
        import demo5
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "healthy",
            "mcp_tools": ["optical-character-recognition", "scan-barcode"],
        }
        with patch("requests.get", return_value=mock_resp):
            result = demo5.call_health("http://localhost:8000")
        assert "healthy" in result


# =============================================================================
# Tests for refactored CodeAnalyzerTool
# =============================================================================

class TestCodeAnalyzerTool:
    """Tests for the refactored app/tools/code_analyzer.py."""

    def setup_method(self):
        import sys
        # Make sure we use the package version
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_analyze_simple_code(self):
        from app.tools.code_analyzer import analyze_code
        result = analyze_code("x = 1\n")
        assert "Lines of Code" in result
        assert "Functions" in result

    def test_analyze_counts_functions(self):
        from app.tools.code_analyzer import analyze_code
        code = "def foo(): pass\ndef bar(): pass\n"
        result = analyze_code(code)
        assert "Functions: 2" in result

    def test_analyze_counts_classes(self):
        from app.tools.code_analyzer import analyze_code
        code = "class Foo:\n    pass\n"
        result = analyze_code(code)
        assert "Classes: 1" in result

    def test_analyze_counts_imports(self):
        from app.tools.code_analyzer import analyze_code
        code = "import os\nfrom sys import argv\n"
        result = analyze_code(code)
        assert "Imports: 2" in result

    def test_analyze_syntax_error_doesnt_crash(self):
        from app.tools.code_analyzer import analyze_code
        result = analyze_code("def (broken\n")
        assert "Lines of Code" in result

    def test_analyze_empty_code(self):
        from app.tools.code_analyzer import analyze_code
        result = analyze_code("")
        assert "Lines of Code: 0" in result

    @pytest.mark.asyncio
    async def test_call_returns_text_content(self):
        from app.tools.code_analyzer import handle_code_analyzer
        result = await handle_code_analyzer({"code": "x = 1\n"})
        assert len(result) == 1
        assert "Code Analysis Results" in result[0].text

    def test_tool_definition_fields(self):
        from app.tools.code_analyzer import CODE_ANALYZER_TOOL
        assert CODE_ANALYZER_TOOL.name == "code_analyzer"
        assert CODE_ANALYZER_TOOL.description is not None
        assert "code" in CODE_ANALYZER_TOOL.inputSchema["properties"]
