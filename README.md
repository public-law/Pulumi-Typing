# Pulumi Typing

Enhanced Python type hints for Pulumi provider SDKs.

This independent project follows upstream Pulumi Python SDK releases, generates companion `.pyi` files, and applies a source-aware transformation. The transformation is intentionally a no-op for now; recovering `Available values:` domains as `Literal` annotations is the next experiment.

## Development

```sh
python -m pip install -e '.[dev]'
pytest
python -m pulumi_typing.sync --package pulumi-cloudflare --output generated
```

The scheduled GitHub Actions workflow checks for upstream SDK changes daily and commits regenerated stubs. Publishing to PyPI is not yet enabled.

## Design

- Follow official released SDKs rather than upstream development commits.
- Keep runtime Pulumi packages unchanged.
- Produce full module stubs as the baseline.
- Track the upstream version in `generated/pulumi_cloudflare-stubs/upstream.json`.
- Add annotation transformations incrementally, with tests.

## First refinement: Ruleset kind

The initial experiment extracts the documented allowed values for
`pulumi_cloudflare.ruleset.RulesetArgs.kind` and narrows its constructor
annotation to `pulumi.Input[Literal[...]]`. The recovered domain is recorded
in `generated/pulumi_cloudflare-stubs/constraints.json` so that upstream
changes appear in ordinary Git diffs.

This is intentionally limited to one declaration. The next iteration can
generalize extraction across fields and constructors, then add type-checker
integration tests. The test fixture is a small excerpt of the actual
Pyright-generated Cloudflare SDK stub, with no mocks.

Run the focused tests using `pytest tests/test_transform.py`.
