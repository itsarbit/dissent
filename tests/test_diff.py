import pytest

from dissent.diff import get_diff


class TestGetDiff:
    def test_raises_on_empty_stdin(self, monkeypatch):
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        with pytest.raises(RuntimeError, match="Empty input"):
            get_diff("-")

    def test_reads_from_stdin(self, monkeypatch):
        import io

        fake_diff = "diff --git a/foo.py b/foo.py\n+hello\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(fake_diff))
        result = get_diff("-")
        assert result == fake_diff
