"""Python code analyzer tool for MCP server.

Analyzes Python code using AST-based parsing to provide metrics
such as function count, class count, import count, lines of code,
and cyclomatic complexity estimates.
"""

import ast
import re
from typing import Any, List

from mcp.types import TextContent, Tool


# Tool definition (used when registering with the MCP server)
CODE_ANALYZER_TOOL = Tool(
    name="code_analyzer",
    description=(
        "Analyze Python code: count functions, classes, imports, "
        "complexity, and suggest improvements"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to analyze",
            }
        },
        "required": ["code"],
    },
)


def analyze_code(code: str) -> str:
    """Analyze Python source code and return a formatted metrics report."""
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
        # Fall back to regex-based counting when the code has syntax errors
        func_count = len(re.findall(r"^\s*(?:async\s+)?def\s+\w+", code, re.MULTILINE))
        class_count = len(re.findall(r"^\s*class\s+\w+", code, re.MULTILINE))
        import_count = len(re.findall(r"^(?:import|from)\s+\w+", code, re.MULTILINE))

    # Lines of code (non-empty, non-comment lines)
    lines = code.split("\n")
    loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])

    # Simple cyclomatic complexity estimate based on branching keywords
    branch_keywords = re.findall(
        r"\b(if|elif|else|for|while|try|except|finally|with|and|or)\b",
        code,
    )
    complexity = min(len(branch_keywords) // 5 + 1, 10)

    # Quality suggestions
    suggestions = []
    if loc > 100:
        suggestions.append("Consider splitting into multiple files (<100 LOC per file)")
    if import_count > 10:
        suggestions.append("Consider grouping imports or using __init__.py")
    if func_count == 0 and loc > 20:
        suggestions.append("Consider extracting logic into named functions for readability")
    if class_count > 5:
        suggestions.append("Large number of classes; consider separate modules per class")

    quality_score = min(10, max(1, 10 - complexity + (loc // 20)))

    result_lines = [
        "Metrics:",
        f"- Lines of Code: {loc}",
        f"- Functions: {func_count}",
        f"- Classes: {class_count}",
        f"- Imports: {import_count}",
        f"- Cyclomatic Complexity: {complexity}/10",
        "",
        f"Quality Score: {quality_score}/10",
        "",
        "Suggestions:",
    ]
    if suggestions:
        result_lines.extend(f"- {s}" for s in suggestions)
    else:
        result_lines.append("- No issues detected")

    return "\n".join(result_lines)


async def handle_code_analyzer(arguments: dict[str, Any]) -> List[TextContent]:
    """MCP tool handler for the code_analyzer tool."""
    code = arguments.get("code", "")
    result = analyze_code(code)
    return [TextContent(type="text", text=f"## Code Analysis Results\n\n{result}")]
