"""CLI entry point for GitHub PR reviews: dissent-pr <PR_URL>."""

import asyncio
import os

import click
from rich.console import Console

from dissent.debate import run_review
from dissent.github import get_pr_diff, parse_pr_url, post_review
from dissent.personas import load_personas


@click.command()
@click.argument("pr_url")
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
    help="Comma-separated list: security,performance,readability,architecture,testing,correctness",
)
@click.option(
    "--persona-file",
    default=None,
    type=click.Path(exists=True),
    help="YAML file with custom persona definitions.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run review but don't post comments. Print results to terminal instead.",
)
def main(
    pr_url,
    model,
    base_url,
    api_key,
    rounds,
    personas,
    persona_file,
    dry_run,
):
    """Review a GitHub PR with swarm intelligence and post inline comments.

    PR_URL is a GitHub pull request URL.

    \b
    Examples:
      dissent-pr https://github.com/owner/repo/pull/123
      dissent-pr https://github.com/owner/repo/pull/123 --dry-run
      dissent-pr https://github.com/owner/repo/pull/123 --personas security,performance
    """
    console = Console()

    model = model or os.environ.get("DISSENT_MODEL", "gpt-4o")
    base_url = base_url or os.environ.get("DISSENT_BASE_URL")
    loaded_personas = load_personas(persona_file)

    # Parse PR URL
    try:
        owner, repo, pr_number = parse_pr_url(pr_url)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from None

    console.print(
        f"[bold]Dissent[/bold] reviewing [cyan]{owner}/{repo}#{pr_number}[/cyan]\n"
    )

    # Fetch diff
    with console.status("[bold]Fetching PR diff..."):
        try:
            diff = get_pr_diff(owner, repo, pr_number)
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1) from None

    # Run review
    persona_names = None
    if personas:
        persona_names = [p.strip() for p in personas.split(",")]

    with console.status("[bold]Swarm reviewing...") as status:

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

    finding_count = len(result["findings"])
    console.print(
        f"[bold]Review complete:[/bold] {finding_count} finding(s) "
        f"after {rounds} round(s) of debate\n"
    )

    if dry_run:
        from dissent.output import print_results

        print_results(result, fmt="terminal", personas=loaded_personas)
        return

    # Post review
    if finding_count == 0:
        console.print("[green]No issues found. Skipping PR comment.[/green]")
        return

    with console.status("[bold]Posting review to GitHub..."):
        try:
            review_url = post_review(owner, repo, pr_number, result)
        except RuntimeError as e:
            console.print(f"[red]Error posting review:[/red] {e}")
            console.print("\nFalling back to terminal output:\n")
            from dissent.output import print_results

            print_results(result, fmt="terminal", personas=loaded_personas)
            raise SystemExit(1) from None

    console.print(f"[green]Review posted:[/green] {review_url}")


if __name__ == "__main__":
    main()
