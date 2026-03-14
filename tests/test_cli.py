from unittest.mock import patch

from click.testing import CliRunner

from dissent.cli import main


class TestCli:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Swarm intelligence for code review" in result.output

    def test_empty_diff_shows_error(self):
        runner = CliRunner()
        result = runner.invoke(main, ["-"], input="")
        assert result.exit_code == 1
        assert "Error" in result.output

    @patch("dissent.cli.run_review")
    def test_runs_with_piped_diff(self, mock_review):
        mock_review.return_value = {
            "findings": [],
            "withdrawn": [],
            "reviewer_count": 5,
            "summary": {
                "consensus": [],
                "split": [],
                "emergent": [],
                "verdict": "clean",
                "total": 0,
                "withdrawn_count": 0,
            },
        }

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-", "--model", "test-model", "--api-key", "fake-key"],
            input="diff --git a/f.py b/f.py\n+hello\n",
        )
        assert result.exit_code == 0
        assert "No issues found" in result.output
        mock_review.assert_called_once()

    @patch("dissent.cli.run_review")
    def test_personas_flag(self, mock_review):
        mock_review.return_value = {
            "findings": [],
            "withdrawn": [],
            "reviewer_count": 2,
            "summary": {
                "consensus": [],
                "split": [],
                "emergent": [],
                "verdict": "clean",
                "total": 0,
                "withdrawn_count": 0,
            },
        }

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-", "--personas", "security,performance", "--api-key", "fake-key"],
            input="diff --git a/f.py b/f.py\n+hello\n",
        )
        assert result.exit_code == 0
        call_kwargs = mock_review.call_args[1]
        assert call_kwargs["persona_names"] == ["security", "performance"]

    @patch("dissent.cli.run_review")
    def test_json_output(self, mock_review):
        mock_review.return_value = {
            "findings": [
                {
                    "title": "Test",
                    "severity": "low",
                    "detail": "x",
                    "source": "security",
                    "endorsements": [],
                    "challenges": [],
                    "consensus_score": 1,
                }
            ],
            "withdrawn": [],
            "reviewer_count": 5,
            "summary": {
                "consensus": [],
                "split": [],
                "emergent": [],
                "verdict": "clean",
                "total": 1,
                "withdrawn_count": 0,
            },
        }

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-", "--output", "json", "--api-key", "fake-key"],
            input="diff --git a/f.py b/f.py\n+hello\n",
        )
        assert result.exit_code == 0
        assert '"title": "Test"' in result.output
