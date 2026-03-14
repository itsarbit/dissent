from dissent.llm import _parse_json


class TestParseJson:
    def test_parses_clean_json(self):
        result = _parse_json('{"findings": []}')
        assert result == {"findings": []}

    def test_parses_json_in_code_block(self):
        text = '```json\n{"findings": [{"title": "test"}]}\n```'
        result = _parse_json(text)
        assert result["findings"][0]["title"] == "test"

    def test_parses_json_in_generic_code_block(self):
        text = '```\n{"findings": []}\n```'
        result = _parse_json(text)
        assert result == {"findings": []}

    def test_extracts_json_from_surrounding_text(self):
        text = 'Here is my analysis:\n{"findings": [{"title": "bug"}]}\nThat is all.'
        result = _parse_json(text)
        assert result["findings"][0]["title"] == "bug"

    def test_returns_empty_findings_on_garbage(self):
        result = _parse_json("this is not json at all")
        assert result == {"findings": []}

    def test_handles_nested_braces(self):
        text = '{"findings": [{"detail": "use {x} syntax"}]}'
        result = _parse_json(text)
        assert len(result["findings"]) == 1
