import json
from pathlib import Path

import pytest

from english_to_gherkin.artifacts import FileBundle, parse_bundle, write_bundle
from english_to_gherkin.errors import ValidationError


def test_parse_and_write_safe_bundle(tmp_path: Path):
    raw = json.dumps({"files": [{"path": "src/test/example.py", "content": "def test_ok():\n    assert True"}]})
    bundle = parse_bundle(raw)
    written = write_bundle(tmp_path, bundle)
    assert written == [tmp_path / "src/test/example.py"]
    assert written[0].read_text(encoding="utf-8").endswith("\n")


@pytest.mark.parametrize(
    "path",
    ["../secret", "/tmp/file", ".github/workflows/attack.yml", "src/.hidden", "src\\file.py"],
)
def test_rejects_unsafe_or_hidden_paths(path: str):
    raw = json.dumps({"files": [{"path": path, "content": "x"}]})
    with pytest.raises(ValidationError):
        parse_bundle(raw)


def test_write_bundle_rejects_escape(tmp_path: Path):
    bundle = FileBundle({"../outside.txt": "x\n"})
    with pytest.raises(Exception, match="escapes repository"):
        write_bundle(tmp_path, bundle)
