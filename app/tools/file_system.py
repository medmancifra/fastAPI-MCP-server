from mcp.types import Tool, TextContent
from typing import List
import os


class FileSystemTool(Tool):
    name = "file_system"
    description = "List project files, read file contents, and get directory structure (safe sandbox)"
    inputSchema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "tree", "read"],
                "description": "Action to perform"
            },
            "path": {
                "type": "string",
                "description": "File or directory path (relative to project root)"
            }
        },
        "required": ["action"]
    }

    SAFE_ROOT = os.path.abspath(".")

    def is_safe_path(self, path: str) -> bool:
        """Prevent directory traversal and absolute paths."""
        full_path = os.path.abspath(path)
        return full_path.startswith(self.SAFE_ROOT)

    async def call(self, action: str, path: str = ".") -> List[TextContent]:
        if not self.is_safe_path(path):
            return [TextContent(type="text", text="❌ Access denied: Unsafe path")]

        if not os.path.exists(path):
            return [TextContent(type="text", text=f"❌ Path does not exist: {path}")]

        if action == "list":
            return self._list_dir(path)
        elif action == "tree":
            return self._tree_view(path)
        elif action == "read":
            return self._read_file(path)
        else:
            return [TextContent(type="text", text="Available actions: list, tree, read")]

    def _list_dir(self, path: str) -> List[TextContent]:
        try:
            items = sorted(os.listdir(path))
            files = [f for f in items if os.path.isfile(os.path.join(path, f))]
            dirs = [d for d in items if os.path.isdir(os.path.join(path, d))]

            content = (
                f"📁 {path}\n"
                f"Files: {len(files)}\n"
                f"Folders: {len(dirs)}\n\n"
                f"📂 Folders:\n" + "\n".join(dirs[:20]) +
                "\n\n📄 Files:\n" + "\n".join(files[:20])
            )

            return [TextContent(type="text", text=content)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _tree_view(self, path: str, max_depth: int = 3) -> List[TextContent]:
        def tree(current_path, prefix="", depth=0):
            if depth > max_depth:
                return []

            tree_str = []
            try:
                items = sorted(os.listdir(current_path))
            except Exception:
                return tree_str

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                item_path = os.path.join(current_path, item)
                connector = "└── " if is_last else "├── "
                tree_str.append(f"{prefix}{connector}{item}")

                if os.path.isdir(item_path):
                    extension = "    " if is_last else "│   "
                    tree_str.extend(
                        tree(item_path, prefix + extension, depth + 1)
                    )

            return tree_str

        tree_lines = tree(path)
        content = f"📁 {path}\n\n" + "\n".join(tree_lines)

        return [TextContent(type="text", text=content)]

    def _read_file(self, path: str) -> List[TextContent]:
        if not os.path.isfile(path):
            return [TextContent(type="text", text=f"❌ Not a file: {path}")]

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2000)

            formatted = (
                f"📄 {path}\n\n"
                "```\n"
                f"{content}\n"
                "```"
            )

            return [TextContent(type="text", text=formatted)]

        except Exception as e:
            return [TextContent(type="text", text=f"Cannot read {path}: {str(e)}")]
