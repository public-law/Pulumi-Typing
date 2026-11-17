"""Conservative, source-documented type refinements for generated stubs."""

import ast
import json
import re
from pathlib import Path

VALUES = re.compile(r'Available values:\s*((?:"[^"]+"(?:,\s*|\s+or\s+)?)+)\.', re.S)
QUOTED = re.compile(r'"([^"]+)"')
KIND_DOCUMENTATION = re.compile(
    r":param\s+[^\n]*\s+kind:\s*[^\n]*\n\s*Available values:[^\n]*"
)
STRING_INPUTS = {"pulumi.Input[_builtins.str]", "pulumi.Input[str]"}
CONSTRAINT_KEY = "pulumi_cloudflare.ruleset.RulesetArgs.kind"


def transform(stub_root: Path, source_root: Path) -> int:
    """Refine RulesetArgs.kind and record its documented allowed values."""
    stub = stub_root / "ruleset.pyi"
    if not stub.exists():
        return 0
    content = stub.read_text()
    ruleset = find_class(ast.parse(content), "RulesetArgs")
    values = documented_kind_values(ruleset)
    if not values:
        return 0
    transformed = refine_kind_annotations(content, ruleset, values)
    if transformed == content:
        return 0
    stub.write_text(transformed)
    write_constraints(stub_root.parent, values)
    return 1


def documented_kind_values(ruleset: ast.ClassDef | None) -> tuple[str, ...]:
    constructor = find_method(ruleset, "__init__")
    if constructor is None:
        return ()
    documentation = ast.get_docstring(constructor) or ""
    match = KIND_DOCUMENTATION.search(documentation)
    return extract_values(match.group()) if match else ()


def refine_kind_annotations(
    content: str, ruleset: ast.ClassDef | None, values: tuple[str, ...]
) -> str:
    annotations = kind_annotations(ruleset)
    positions = editable_annotations(content, annotations)
    if not positions:
        return content
    replacement = literal_input(values)
    for start, end in sorted(positions, reverse=True):
        content = content[:start] + replacement + content[end:]
    return ensure_literal_import(content)


def kind_annotations(ruleset: ast.ClassDef | None) -> list[ast.expr]:
    constructor = find_method(ruleset, "__init__")
    argument = find_argument(constructor, "kind", keyword_only=True)
    if argument is None or argument.annotation is None:
        return []
    annotations = [argument.annotation]
    getter = find_method(ruleset, "kind", setter=False)
    setter = find_method(ruleset, "kind", setter=True)
    if getter is not None and getter.returns is not None:
        annotations.append(getter.returns)
    value = find_argument(setter, "value")
    if value is not None and value.annotation is not None:
        annotations.append(value.annotation)
    return annotations


def editable_annotations(
    content: str, annotations: list[ast.expr]
) -> list[tuple[int, int]]:
    lines = content.splitlines(keepends=True)
    return [
        annotation_span(lines, annotation)
        for annotation in annotations
        if ast.get_source_segment(content, annotation) in STRING_INPUTS
    ]


def annotation_span(lines: list[str], node: ast.expr) -> tuple[int, int]:
    start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    return start, end


def literal_input(values: tuple[str, ...]) -> str:
    return "pulumi.Input[Literal[" + ", ".join(map(repr, values)) + "]]"


def ensure_literal_import(content: str) -> str:
    if "from typing import Literal" in content:
        return content
    return content.replace("from typing import ", "from typing import Literal, ", 1)


def write_constraints(directory: Path, values: tuple[str, ...]) -> None:
    report = {CONSTRAINT_KEY: {
        "type": "string",
        "allowed_values": list(values),
        "source": "generated SDK docstring",
    }}
    (directory / "constraints.json").write_text(json.dumps(report, indent=2) + "\n")


def extract_values(documentation: str) -> tuple[str, ...]:
    """Extract a closed list of quoted values, or return empty if ambiguous."""
    match = VALUES.search(documentation)
    if not match:
        return ()
    values = tuple(QUOTED.findall(match.group(1)))
    return values if len(values) >= 2 and len(values) == len(set(values)) else ()


def find_class(tree: ast.Module, name: str) -> ast.ClassDef | None:
    return next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name),
        None,
    )


def find_method(
    owner: ast.ClassDef | None, name: str, setter: bool = False
) -> ast.FunctionDef | None:
    if owner is None:
        return None
    return next(
        (node for node in owner.body if is_method(node, name, setter)),
        None,
    )


def is_method(node: ast.stmt, name: str, setter: bool) -> bool:
    if not isinstance(node, ast.FunctionDef) or node.name != name:
        return False
    return has_setter_decorator(node) == setter


def has_setter_decorator(method: ast.FunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Attribute) and decorator.attr == "setter"
        for decorator in method.decorator_list
    )


def find_argument(
    method: ast.FunctionDef | None, name: str, keyword_only: bool = False
) -> ast.arg | None:
    if method is None:
        return None
    arguments = method.args.kwonlyargs if keyword_only else method.args.args
    return next((argument for argument in arguments if argument.arg == name), None)
