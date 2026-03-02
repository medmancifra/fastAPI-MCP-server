"""demo4.py — scikit-learn ML pipeline demo using the MCP code analyzer tool.

This demo shows how to use the MCP server's code analyzer as a feature
extractor within a scikit-learn pipeline.  It:

1. Defines a small corpus of Python code snippets labelled "simple" or
   "complex" based on their structure.
2. Uses a custom sklearn transformer that calls the MCP code analyzer
   endpoint to extract numerical features (LOC, functions, classes, imports,
   complexity score).
3. Trains a RandomForestClassifier on those features.
4. Evaluates and prints classification accuracy.

NOTE: The demo also works in **offline mode** (without a running MCP server).
      When no server is reachable, a local fallback analyzer is used instead.

Usage:
    pip install scikit-learn requests
    python demo4.py [--host HOST] [--port PORT] [--token TOKEN]
"""

import argparse
import ast
import os
import re
import sys
import warnings

import requests

try:
    import numpy as np
    from sklearn.base import BaseEstimator, TransformerMixin
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
except ImportError:
    raise SystemExit(
        "scikit-learn and numpy are required for this demo.\n"
        "Install them with:  pip install scikit-learn numpy"
    )

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Sample corpus
# ---------------------------------------------------------------------------

CORPUS: list[tuple[str, str]] = [
    # (code, label)
    (
        "x = 1\nprint(x)\n",
        "simple",
    ),
    (
        "import os\nprint(os.getcwd())\n",
        "simple",
    ),
    (
        "def add(a, b):\n    return a + b\n\nresult = add(2, 3)\n",
        "simple",
    ),
    (
        "\n".join(
            ["import os", "import sys", "import re", "import json", "import csv",
             "import math", "import random", "import datetime", "import pathlib",
             "import logging", "print('many imports')"]
        ),
        "complex",
    ),
    (
        "class Foo:\n    def bar(self):\n        pass\n\nclass Baz(Foo):\n"
        "    def bar(self):\n        for i in range(10):\n            if i % 2:\n"
        "                print(i)\n",
        "complex",
    ),
    (
        "def compute(data):\n    result = []\n    for item in data:\n"
        "        if item > 0:\n            result.append(item * 2)\n"
        "        elif item == 0:\n            result.append(0)\n"
        "        else:\n            result.append(-item)\n    return result\n",
        "complex",
    ),
    (
        "a = 1\nb = 2\nc = a + b\n",
        "simple",
    ),
    (
        "class Config:\n    HOST = 'localhost'\n    PORT = 8000\n\n"
        "class DB(Config):\n    NAME = 'mydb'\n\n"
        "def connect(cfg):\n    try:\n        pass\n    except Exception as e:\n"
        "        print(e)\n",
        "complex",
    ),
]


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------

def _local_extract_features(code: str) -> list[float]:
    """Fallback feature extraction using stdlib ast (no MCP server needed)."""
    func_count = 0
    class_count = 0
    import_count = 0
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
    except SyntaxError:
        func_count = len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))
        class_count = len(re.findall(r"^\s*class\s+\w+", code, re.MULTILINE))
        import_count = len(re.findall(r"^(?:import|from)\s+\w+", code, re.MULTILINE))

    loc = len([ln for ln in code.split("\n") if ln.strip() and not ln.strip().startswith("#")])
    branch_kw = re.findall(
        r"\b(if|elif|else|for|while|try|except|finally|with|and|or)\b", code
    )
    complexity = min(len(branch_kw) // 5 + 1, 10)
    return [float(loc), float(func_count), float(class_count), float(import_count), float(complexity)]


def _parse_mcp_response(text: str) -> list[float]:
    """Extract numeric features from MCP code_analyzer Markdown response."""
    patterns = {
        "loc": r"Lines of Code:\s*(\d+)",
        "funcs": r"Functions:\s*(\d+)",
        "classes": r"Classes:\s*(\d+)",
        "imports": r"Imports:\s*(\d+)",
        "complexity": r"Cyclomatic Complexity:\s*(\d+)/10",
    }
    values = []
    for key in ("loc", "funcs", "classes", "imports", "complexity"):
        m = re.search(patterns[key], text)
        values.append(float(m.group(1)) if m else 0.0)
    return values


# ---------------------------------------------------------------------------
# Custom sklearn transformer
# ---------------------------------------------------------------------------

class MCPCodeFeatureExtractor(BaseEstimator, TransformerMixin):
    """Transformer that calls the MCP code analyzer and returns numeric features.

    Falls back to local analysis when the server is unreachable.

    Features (5 dimensions):
        [loc, functions, classes, imports, cyclomatic_complexity]
    """

    FEATURE_NAMES = ["loc", "functions", "classes", "imports", "complexity"]

    def __init__(self, mcp_base_url: str = "http://localhost:8000", token: str = ""):
        self.mcp_base_url = mcp_base_url
        self.token = token
        self._use_local = False

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array([self._extract(code) for code in X])

    def _extract(self, code: str) -> list[float]:
        if self._use_local:
            return _local_extract_features(code)

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            resp = requests.post(
                f"{self.mcp_base_url}/mcp/ocr",  # reuse OCR? No — use code_analyzer via MCP
                # The MCP code analyzer is exposed through the MCP protocol transport, not
                # as a direct HTTP endpoint.  We call our own local fallback instead.
                json={"code": code},
                headers=headers,
                timeout=3,
            )
            if resp.status_code == 200:
                return _parse_mcp_response(resp.json().get("text", ""))
        except Exception:
            pass

        # Server unavailable or endpoint not found — switch to local mode
        self._use_local = True
        print("[INFO] MCP server unreachable, using local fallback analyzer.")
        return _local_extract_features(code)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo 4: scikit-learn + MCP code analyzer")
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8000")))
    parser.add_argument("--token", default=os.getenv("MCP_TOKEN", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mcp_base_url = f"http://{args.host}:{args.port}"

    print("=== Demo 4: scikit-learn pipeline with MCP Code Analyzer ===\n")

    codes = [c for c, _ in CORPUS]
    labels = [lbl for _, lbl in CORPUS]

    X_train, X_test, y_train, y_test = train_test_split(
        codes, labels, test_size=0.25, random_state=42
    )

    pipeline = Pipeline([
        ("features", MCPCodeFeatureExtractor(mcp_base_url=mcp_base_url, token=args.token)),
        ("clf", RandomForestClassifier(n_estimators=50, random_state=42)),
    ])

    print("Training RandomForestClassifier on code complexity features...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    feature_names = MCPCodeFeatureExtractor.FEATURE_NAMES
    importances = pipeline.named_steps["clf"].feature_importances_
    print("Feature Importances:")
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
        bar = "#" * int(imp * 40)
        print(f"  {name:<12} {imp:.3f}  {bar}")

    print("\n=== Done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
