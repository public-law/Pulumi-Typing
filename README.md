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
