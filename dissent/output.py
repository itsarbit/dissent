import json

from rich.console import Console
from rich.panel import Panel

from dissent.personas import DEFAULT_PERSONAS as PERSONAS


def print_results(
    consensus: dict, fmt: str = "terminal", personas: dict | None = None
) -> None:
    if personas:
        # Temporarily swap in custom personas for display
        global PERSONAS
        PERSONAS = personas
    if fmt == "json":
        print(json.dumps(consensus, indent=2))
        return
    if fmt == "markdown":
        _print_markdown(consensus)
        return
    _print_terminal(consensus)


def _print_terminal(consensus: dict) -> None:
    console = Console()
    findings = consensus["findings"]
    withdrawn = consensus["withdrawn"]
    reviewer_count = consensus["reviewer_count"]

    if not findings:
        console.print(
            "\n[green bold]No issues found.[/green bold] "
            "All reviewers agree the code looks good.\n"
        )
        return

    console.print()
    console.print(
        f"[bold]Dissent[/bold]  {reviewer_count} agents, {len(findings)} finding(s)\n"
    )

    sev_colors = {"high": "red", "medium": "yellow", "low": "blue"}

    for i, f in enumerate(findings, 1):
        severity = f.get("severity", "low")
        sev_color = sev_colors.get(severity, "white")

        source_persona = PERSONAS.get(f.get("source", ""), {})
        source_color = source_persona.get("color", "white")
        source_name = source_persona.get("name", f.get("source", "unknown"))

        endorsements = f.get("endorsements", [])
        challenges = f.get("challenges", [])
        score = f.get("consensus_score", 0)

        header = (
            f"#{i}  [{sev_color} bold]{severity.upper()}"
            f"[/{sev_color} bold]  {f.get('title', 'Untitled')}"
        )

        body_parts: list[str] = []

        if f.get("file"):
            loc = f["file"]
            if f.get("line"):
                loc += f":{f['line']}"
            body_parts.append(f"[dim]{loc}[/dim]")

        body_parts.append(f.get("detail", ""))

        if f.get("suggestion"):
            body_parts.append(f"\n[bold]Suggestion:[/bold] {f['suggestion']}")

        if endorsements:
            names = ", ".join(
                PERSONAS.get(e["reviewer"], {}).get("name", e["reviewer"])
                for e in endorsements
            )
            body_parts.append(f"\n[green]Endorsed by: {names}[/green]")

        if challenges:
            for c in challenges:
                challenger = PERSONAS.get(c["reviewer"], {}).get("name", c["reviewer"])
                body_parts.append(
                    f"\n[red]Challenged by {challenger}:[/red] {c.get('reason', '')}"
                )

        from_debate = (
            " [dim](surfaced during debate)[/dim]" if f.get("from_debate") else ""
        )
        subtitle = (
            f"Found by [{source_color}]{source_name}[/{source_color}]"
            f"{from_debate}  |  Consensus: {score}"
        )

        console.print(
            Panel(
                "\n".join(body_parts),
                title=header,
                subtitle=subtitle,
                border_style=sev_color,
            )
        )

    if withdrawn:
        console.print(
            f"\n[dim]{len(withdrawn)} finding(s) withdrawn during debate.[/dim]"
        )

    # Swarm summary
    summary = consensus.get("summary", {})
    if summary:
        _print_swarm_summary(console, summary)

    console.print()


def _print_swarm_summary(console: Console, summary: dict) -> None:
    console.print()
    console.print(
        Panel(
            _build_summary_body(summary),
            title="[bold]Swarm Summary[/bold]",
            border_style="bright_black",
        )
    )


def _build_summary_body(summary: dict) -> str:
    parts = [f"[bold]Verdict:[/bold] {summary.get('verdict', 'N/A')}"]

    consensus = summary.get("consensus", [])
    if consensus:
        items = ", ".join(consensus[:5])
        parts.append(f"\n[green]Swarm agrees on:[/green] {items}")

    split = summary.get("split", [])
    if split:
        items = ", ".join(split[:5])
        parts.append(f"\n[yellow]Swarm split on:[/yellow] {items}")

    emergent = summary.get("emergent", [])
    if emergent:
        items = ", ".join(emergent[:5])
        parts.append(f"\n[cyan]Emerged from debate:[/cyan] {items}")

    withdrawn_count = summary.get("withdrawn_count", 0)
    if withdrawn_count:
        parts.append(
            f"\n[dim]{withdrawn_count} finding(s) withdrawn "
            f"(agents changed their minds)[/dim]"
        )

    return "\n".join(parts)


def _print_markdown(consensus: dict) -> None:
    findings = consensus["findings"]

    if not findings:
        print("# Dissent: No Issues Found\n\nAll reviewers agree the code looks good.")
        return

    print("# Dissent Results\n")
    print(
        f"**{consensus['reviewer_count']} agents** | **{len(findings)} finding(s)**\n"
    )

    for i, f in enumerate(findings, 1):
        severity = f.get("severity", "low").upper()
        print(f"## #{i} [{severity}] {f.get('title', 'Untitled')}\n")

        if f.get("file"):
            loc = f["file"]
            if f.get("line"):
                loc += f":{f['line']}"
            print(f"**Location:** `{loc}`\n")

        print(f"{f.get('detail', '')}\n")

        if f.get("suggestion"):
            print(f"**Suggestion:** {f['suggestion']}\n")

        endorsements = f.get("endorsements", [])
        challenges = f.get("challenges", [])

        if endorsements:
            names = ", ".join(e["reviewer"] for e in endorsements)
            print(f"**Endorsed by:** {names}\n")

        if challenges:
            for c in challenges:
                print(f"**Challenged by {c['reviewer']}:** {c.get('reason', '')}\n")

        print(f"*Consensus score: {f.get('consensus_score', 0)}*\n")
        print("---\n")
