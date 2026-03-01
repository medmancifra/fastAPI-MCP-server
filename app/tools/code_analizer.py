from mcp.types import Tool, TextContent
from tree_sitter import Language, Parser
from typing import List, Dict, Any
import re

Language.build_library(
    'build/my-languages.so',
    ['tree-sitter-python']
)

PY_LANGUAGE = Language('build/my-languages.so', 'python')
parser = Parser()
parser.set_language(PY_LANGUAGE)

class CodeAnalyzerTool(Tool):
    name = "code_analyzer"
    description = "Analyze Python code: count functions, classes, imports, complexity, and suggest improvements"
    inputSchema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to analyze"
            }
        },
        "required": ["code"]
    }

    async def call(self, code: str) -> List[TextContent]:
        analysis = self.analyze_code(code)
        return [TextContent(type="text", text=f"## Code Analysis Results\n\n{analysis}")]
    
    def analyze_code(self, code: str) -> str:
        # Parse AST
        try:
            tree = parser.parse(bytes(code, "utf8"))
        except:
            tree = None
        
        # Count functions and classes
        func_count = len(tree.root_node.children) if tree else 0
        class_count = len([n for n in tree.root_node.children if n.type == 'class_definition']) if tree else 0
        
        # Count imports
        import_count = len(re.findall(r'^import|from\s+\w+', code, re.MULTILINE))
        
        # Lines of code and complexity
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        complexity = min(loc // 10 + 1, 10)
        
        # Suggestions
        suggestions = []
        if loc > 100:
            suggestions.append("Consider splitting into multiple files (<100 LOC per file)")
        if import_count > 10:
            suggestions.append("Consider grouping imports or using init.py")
        
        result = f"""
Metrics:
- Lines of Code: {loc}
- Functions: {func_count}
- Classes: {class_count}
- Imports: {import_count}
- Cyclomatic Complexity: {complexity}/10

Quality Score: {min(10, max(1, 10 - complexity + (loc//20)))}/10

Suggestions:
"""
        for suggestion in suggestions:
            result += f"- {suggestion}\n"
            
        return result.strip()
