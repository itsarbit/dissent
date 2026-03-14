import asyncio
import os

import click
from rich.console import Console

from dissent.debate import run_review
from dissent.diff import get_diff
from dissent.output import print_results
from dissent.personas import load_personas


@click.command()
@click.argument("target", default="HEAD~1")
@click.option("--staged", is_flag=True, help="Review staged changes.")
@click.option(
    "--model",
    default=None,
    help="Model name (default: gpt-4o). Env: DISSENT_MODEL",
)
@click.option(
    "--base-url",
    default=None,
    help="API base URL, e.g. http://localhost:11434/v1 for Ollama. Env: DISSENT_BASE_URL",
)
@click.option(
    "--api-key",
    default=None,
    help="API key. Defaults to OPENAI_API_KEY env var.",
)
@click.option(
    "--rounds",
    default=2,
    type=int,
    show_default=True,
    help="Number of debate rounds.",
)
@click.option(
    "--personas",
    default=None,
    help="Comma-separated list: security,performance,readability,architecture,testing",
)
@click.option(
    "--persona-file",
    default=None,
    type=click.Path(exists=True),
    help="YAML file with custom persona definitions. Also checks .dissent.yaml in cwd.",
)
@click.option(
    "--output",
    "output_format",
    default="terminal",
    type=click.Choice(["terminal", "json", "markdown"]),
    show_default=True,
    help="Output format.",
)
def main(
    target,
    staged,
    model,
    base_url,
    api_key,
    rounds,
    personas,
    persona_file,
    output_format,
):
    """Swarm intelligence for code review - diverse expert agents that debate.

    TARGET is a git diff target (default: HEAD~1). Use '-' for stdin.

    \b
    Examples:
      dissent HEAD~1
      dissent abc123..def456
      dissent --staged
      dissent --persona-file my_team.yaml HEAD~1
      git diff main | dissent -
      dissent --model llama3 --base-url http://localhost:11434/v1 HEAD~3
    """
    console = Console()

    model = model or os.environ.get("DISSENT_MODEL", "gpt-4o")
    base_url = base_url or os.environ.get("DISSENT_BASE_URL")

    # Load personas
    loaded_personas = load_personas(persona_file)

    try:
        diff = get_diff(target if not staged else None, staged=staged)
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from None

    persona_names = None
    if personas:
        persona_names = [p.strip() for p in personas.split(",")]

    with console.status("[bold]Dissent assembling reviewers...") as status:

        def on_status(msg: str) -> None:
            status.update(f"[bold]{msg}")

        result = asyncio.run(
            run_review(
                diff=diff,
                model=model,
                base_url=base_url,
                api_key=api_key,
                rounds=rounds,
                persona_names=persona_names,
                personas_dict=loaded_personas,
                on_status=on_status,
            )
        )

    print_results(result, fmt=output_format, personas=loaded_personas)


if __name__ == "__main__":
    main()
