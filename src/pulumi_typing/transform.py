from pathlib import Path


def transform(stub_root: Path, source_root: Path) -> int:
    """Placeholder for source-aware annotation refinement.

    Return the number of changed declarations. Currently a no-op.
    """
    assert stub_root.is_dir()
    assert source_root.is_dir()
    return 0
