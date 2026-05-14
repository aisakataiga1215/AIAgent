import typer
from rich.console import Console

app = typer.Typer(
    name="devflow",
    help="DevFlow AI — Multi-Agent Development Workflow System",
    add_completion=False,
)
console = Console()


@app.callback()
def callback() -> None:
    """DevFlow AI — automate code review, test generation, and documentation."""


@app.command()
def review(
    repo: str = typer.Option(".", "--repo", "-r", help="Path to the repository"),
    pr: int = typer.Option(None, "--pr", "-p", help="PR number to review"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch to review"),
    output: str = typer.Option("terminal", "--output", "-o", help="Output format: terminal|markdown|json"),
) -> None:
    """Run the Code Review Agent on a repository, PR, or branch."""
    console.print(f"[bold blue]DevFlow Review[/bold blue]")
    console.print(f"  Repo: {repo}")
    if pr:
        console.print(f"  PR: #{pr}")
    if branch:
        console.print(f"  Branch: {branch}")
    console.print()
    console.print("[yellow]Code Review Agent — coming in Phase 3[/yellow]")


@app.command()
def workflow(
    name: str = typer.Argument("pr-review", help="Workflow name to run"),
    repo: str = typer.Option(".", "--repo", "-r", help="Path to the repository"),
) -> None:
    """Run a multi-agent workflow (e.g. pr-review, full-ci, doc-sync)."""
    console.print(f"[bold blue]DevFlow Workflow: {name}[/bold blue]")
    console.print(f"  Repo: {repo}")
    console.print()
    console.print("[yellow]Workflow Engine — coming in Phase 6[/yellow]")


@app.command()
def ingest(
    repo: str = typer.Option(".", "--repo", "-r", help="Path to the repository to index"),
    reset: bool = typer.Option(False, "--reset", help="Clear existing index before ingestion"),
) -> None:
    """Index a codebase into the knowledge base for RAG retrieval."""
    console.print(f"[bold blue]DevFlow Ingest[/bold blue]")
    console.print(f"  Repo: {repo}")
    console.print()
    console.print("[yellow]RAG Ingestion — coming in Phase 4[/yellow]")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the DevFlow API server."""
    console.print(f"[bold blue]DevFlow Server[/bold blue]")
    console.print(f"  Starting at http://{host}:{port}")
    console.print()
    console.print("[yellow]API Server — coming in Phase 7[/yellow]")


if __name__ == "__main__":
    app()
