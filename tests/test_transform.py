from pulumi_typing.transform import transform


def test_placeholder_transform_is_noop(tmp_path):
    stubs = tmp_path / "stubs"
    sources = tmp_path / "sources"
    stubs.mkdir()
    sources.mkdir()
    assert transform(stubs, sources) == 0
