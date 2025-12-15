import os
import sys
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich import print

console = Console()

def main():
    console.clear()
    console.print("[bold blue]🧪 Orak Experiment Runner[/bold blue]", justify="center")
    console.print()

    # 1. Choose Mode
    mode = Prompt.ask("Select Mode", choices=["local", "submission"], default="local")
    is_local = mode == "local"

    # 2. Choose Games
    available_games = [
        "twenty_fourty_eight",
        "super_mario",
        "pokemon_red",
        "star_craft",
    ]
    
    console.print("\n[bold]Available Games:[/bold]")
    for i, game in enumerate(available_games):
        console.print(f"{i+1}. {game}")
    
    selected_indices_str = Prompt.ask(
        "\nSelect games to run (comma separated numbers, e.g. 1,3) or 'all'", 
        default="all"
    )

    if selected_indices_str.lower() == "all":
        selected_games = [] # Empty list implies all games in the underlying runner logic if not specified, 
                            # BUT the runner logic says: "In remote/submission mode, all games are always evaluated."
                            # For local mode w/ --games, we need to specify them.
                            # Actually, if we pass NO --games arg, it runs all. 
        games_arg = []
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selected_indices_str.split(",")]
            selected_games = [available_games[i] for i in indices if 0 <= i < len(available_games)]
            games_arg = ["--games"] + selected_games
        except (ValueError, IndexError):
            console.print("[red]Invalid selection. Defaulting to ALL games.[/red]")
            games_arg = []

    # 3. Plain Logs Option
    plain_logs = Confirm.ask("Use plain logs (disable live UI)?", default=False)
    
    # 4. Construct Command
    # Base command: uv run python run.py
    cmd = ["uv", "run", "python", "run.py"]
    
    if is_local:
        cmd.append("--local")
        if games_arg:
            cmd.extend(games_arg)
    
    # Environment variables
    env = os.environ.copy()
    if plain_logs:
        env["ORAK_PLAIN_LOGS"] = "1"

    console.print("\n[bold green]🚀 Launching Experiment...[/bold green]")
    console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")
    console.print()

    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"\n[bold red]Experiment failed with exit code {e.returncode}[/bold red]")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Experiment interrupted by user.[/bold yellow]")

if __name__ == "__main__":
    main()
