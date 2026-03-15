import os
import tempfile

from dissent.personas import DEFAULT_PERSONAS, load_personas


class TestDefaultPersonas:
    def test_has_six_built_in_personas(self):
        assert len(DEFAULT_PERSONAS) == 6

    def test_all_personas_have_required_keys(self):
        required = {"name", "icon", "color", "system"}
        for key, persona in DEFAULT_PERSONAS.items():
            missing = required - set(persona.keys())
            assert not missing, f"Persona '{key}' missing keys: {missing}"

    def test_persona_names(self):
        expected = {
            "security", "performance", "readability",
            "architecture", "testing", "correctness",
        }
        assert set(DEFAULT_PERSONAS.keys()) == expected


class TestLoadPersonas:
    def test_returns_defaults_when_no_file(self):
        personas = load_personas(None)
        assert personas is DEFAULT_PERSONAS

    def test_loads_from_yaml_file(self):
        yaml_content = """
custom_reviewer:
  name: Custom
  color: cyan
  prompt: "You review code for custom things."
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                personas = load_personas(f.name)
                assert "custom_reviewer" in personas
                assert personas["custom_reviewer"]["name"] == "Custom"
                assert personas["custom_reviewer"]["color"] == "cyan"
                assert (
                    personas["custom_reviewer"]["system"]
                    == "You review code for custom things."
                )
            finally:
                os.unlink(f.name)

    def test_assigns_default_color_and_icon(self):
        yaml_content = """
minimal:
  prompt: "You review code."
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                personas = load_personas(f.name)
                assert personas["minimal"]["name"] == "Minimal"
                assert personas["minimal"]["icon"] == "[MINI]"
                assert personas["minimal"]["color"]  # some color assigned
            finally:
                os.unlink(f.name)
