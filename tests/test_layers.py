import ast
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "src/job_processor"

# web may import service. service may import data. Nothing imports upward,
# web never imports data, and database details never leave data.
FORBIDDEN_IMPORTS = {
    "web": ("job_processor.data", "sqlalchemy", "job_processor.main"),
    "service": (
        "fastapi",
        "starlette",
        "sqlalchemy",
        "job_processor.web",
        "job_processor.main",
    ),
    "data": ("fastapi", "starlette", "job_processor.service", "job_processor.web"),
}


def imported_modules(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("layer", list(FORBIDDEN_IMPORTS))
def test_each_layer_imports_only_what_it_may(layer: str) -> None:
    for path in sorted((SOURCE / layer).rglob("*.py")):
        for module in imported_modules(path):
            for forbidden in FORBIDDEN_IMPORTS[layer]:
                assert not module.startswith(forbidden), (
                    f"{layer}/{path.name} imports {module}"
                )
