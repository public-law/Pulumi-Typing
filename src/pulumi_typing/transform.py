"""Conservative, source-documented type refinements for generated stubs."""

import ast
import json
import re
from pathlib import Path

VALUES = re.compile(r'Available values:\s*((?:"[^"]+"(?:,\s*|\s+or\s+)?)+)\.', re.S)
QUOTED = re.compile(r'"([^"]+)"')


def extract_values(documentation: str) -> tuple[str, ...]:
    """Extract a closed list of quoted values, or return empty if ambiguous."""
    match = VALUES.search(documentation)
    if not match:
        return ()
    values = tuple(QUOTED.findall(match.group(1)))
    return values if len(values) >= 2 and len(values) == len(set(values)) else ()


def transform(stub_root: Path, source_root: Path) -> int:
    """Refine RulesetArgs.kind using its generated SDK documentation.

    This deliberately tiny first transformation preserves all other annotations.
    It records the recovered domain in JSON for Git diffs.
    """
    stub = stub_root / "ruleset.pyi"
    if not stub.exists():
        return 0
    content = stub.read_text()
    tree = ast.parse(content)
    target = next((node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "RulesetArgs"), None)
    if target is None:
        return 0
    constructor = next((node for node in target.body
                        if isinstance(node, ast.FunctionDef) and node.name == "__init__"), None)
    if constructor is None:
        return 0
    doc = ast.get_docstring(constructor) or ""
    match = re.search(r":param\s+[^\n]*\s+kind:\s*[^\n]*\n\s*Available values:[^\n]*", doc)
    values = extract_values(match.group(0)) if match else ()
    if not values:
        return 0
    arg = next((a for a in constructor.args.kwonlyargs if a.arg == "kind"), None)
    if arg is None or arg.annotation is None:
        return 0
    annotation = ast.get_source_segment(content, arg.annotation)
    if annotation not in ("pulumi.Input[_builtins.str]", "pulumi.Input[str]"):
        return 0
    replacement = "pulumi.Input[Literal[" + ", ".join(repr(v) for v in values) + "]]"
    lines = content.splitlines(keepends=True)
    start = sum(len(line) for line in lines[:arg.annotation.lineno - 1]) + arg.annotation.col_offset
    end = sum(len(line) for line in lines[:arg.annotation.end_lineno - 1]) + arg.annotation.end_col_offset
    content = content[:start] + replacement + content[end:]
    content = content.replace("from typing import ", "from typing import Literal, ", 1)
    stub.write_text(content)
    report = {
        "pulumi_cloudflare.ruleset.RulesetArgs.kind": {
            "type": "string",
            "allowed_values": list(values),
            "source": "generated SDK docstring",
        }
    }
    (stub_root.parent / "constraints.json").write_text(json.dumps(report, indent=2) + "\n")
    return 1
