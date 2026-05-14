import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.config import settings

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
    if not settings.anthropic_api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set. Create a .env file or set the environment variable.[/red]")
        raise typer.Exit(code=1)

    from src.agents.code_review import review_repository

    target = "HEAD~1"
    if branch:
        target = branch
    elif pr:
        target = f"origin/main..HEAD"

    console.print(f"[bold blue]DevFlow Review[/bold blue]")
    console.print(f"  Repo: {repo}  Target: {target}")
    console.print()

    with console.status("[bold green]Code Review Agent analyzing...[/bold green]"):
        result = asyncio.run(review_repository(workspace=repo, target=target))

    console.print()
    if result.success:
        if output == "json":
            import json
            console.print(json.dumps({"content": result.content, "tool_calls": result.tool_calls, "tokens": result.tokens_used}, indent=2))
        elif output == "markdown":
            console.print(result.content)
        else:
            console.print(Panel(Markdown(result.content), title="Code Review", border_style="blue"))
        console.print(f"[dim]Tool calls: {result.tool_calls} | Tokens: {result.tokens_used}[/dim]")
    else:
        console.print(f"[red]Review failed: {result.content}[/red]")
        for step in result.steps:
            console.print(f"[dim]  Step {step.iteration}: action={step.action}, success={bool(step.observation)}[/dim]")


@app.command()
def workflow(
    name: str = typer.Argument("pr-review", help="Workflow name to run"),
    repo: str = typer.Option(".", "--repo", "-r", help="Path to the repository"),
) -> None:
    """Run a multi-agent workflow (e.g. pr-review, full-ci)."""
    from src.workflow.templates import WORKFLOW_TEMPLATES
    from src.workflow.state import WorkflowState
    from src.workflow.nodes import orchestrator_node, code_review_node, aggregate_node

    if name not in WORKFLOW_TEMPLATES:
        console.print(f"[red]Unknown workflow: {name}. Available: {list(WORKFLOW_TEMPLATES.keys())}[/red]")
        raise typer.Exit(code=1)

    template = WORKFLOW_TEMPLATES[name](repo=repo)

    console.print(f"[bold blue]DevFlow Workflow: {name}[/bold blue]")
    console.print(f"  Repo: {repo}")
    console.print()

    state: WorkflowState = {
        "messages": [],
        "task": template["task"],
        "plan": template["plan"],
        "agent_outputs": {},
        "errors": [],
        "status": "pending",
        "metadata": template["metadata"],
    }

    async def _run():
        state_update = await orchestrator_node(state)
        state.update(state_update)

        for p in state["plan"]:
            if p["agent"] == "code_review":
                update = await code_review_node(state)
                state.update(update)

        final = await aggregate_node(state)
        state.update(final)
        return state

    with console.status("[bold green]Running workflow...[/bold green]"):
        result = asyncio.run(_run())

    console.print()
    console.print(Panel(Markdown(result["messages"][-1]["content"] if result["messages"] else "No output"), title=f"Workflow Result: {name}", border_style="blue"))
    console.print(f"[dim]Status: {result['status']}[/dim]")


@app.command()
def ingest(
    repo: str = typer.Option(".", "--repo", "-r", help="Path to the repository to index"),
    reset: bool = typer.Option(False, "--reset", help="Clear existing index before ingestion"),
) -> None:
    """Index a codebase into the knowledge base for RAG retrieval."""
    from src.rag.ingestion import ingest_codebase

    console.print(f"[bold blue]DevFlow Ingest[/bold blue]")
    console.print(f"  Repo: {repo}")

    with console.status("[bold green]Indexing codebase...[/bold green]"):
        count = asyncio.run(ingest_codebase(root=repo, reset=reset))

    console.print(f"[green]Indexed {count} chunks from {repo}[/green]")
    if count == 0:
        console.print("[yellow]No chunks were indexed. Check that the directory contains supported files.[/yellow]")


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
