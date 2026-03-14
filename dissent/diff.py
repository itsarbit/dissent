import subprocess
import sys


def get_diff(target: str | None = None, staged: bool = False) -> str:
    """Get a diff from git or stdin.

    Args:
        target: A git diff target (commit, range, etc.) or "-" for stdin.
        staged: If True, review staged changes instead.

    Returns:
        The diff as a string.
    """
    if target == "-":
        content = sys.stdin.read()
        if not content.strip():
            raise RuntimeError("Empty input from stdin. Pipe in a diff.")
        return content

    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    elif target:
        cmd.append(target)
    else:
        cmd.append("HEAD~1")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr.strip()}")

    if not result.stdout.strip():
        raise RuntimeError("Empty diff. Nothing to review.")

    return result.stdout
