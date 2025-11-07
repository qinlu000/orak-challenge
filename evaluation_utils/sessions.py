import requests
import time
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn

from evaluation_utils.commons import BASE_URL, API_TOKEN, console


class Session:
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id
    
    def create(self):
        with console.status("[bold]Creating session...[/bold]"):
            response = requests.post(
                f"{BASE_URL}/sessions",
                headers={"Authorization": f"Token {API_TOKEN}"}
            )
            response.raise_for_status()
            self.session_id = response.json()["task_id"]
            submission_id = response.json()["submission_id"]
        console.print(Panel.fit(Text(f"Session created: {self.session_id}\nSubmission ID: {submission_id}", style="green"), title="Session"))
    
    def get(self):
        response = requests.get(
            f"{BASE_URL}/sessions/{self.session_id}",
            headers={"Authorization": f"Token {API_TOKEN}"}
        )
        return response.json()
    
    def stop(self):
        response = requests.delete(
            f"{BASE_URL}/sessions/{self.session_id}",
            headers={"Authorization": f"Token {API_TOKEN}"}
        )
        return response.json()
    
    def wait_for_start(self, poll_interval: float = 1.0, timeout: float = 300.0):
        start = time.time()
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Waiting for game server instance to start...", start=True)
            while True:
                status = self.get()["last_status"]
                progress.update(task, description=f"Game server instance: [bold]{status}[/bold]")
                if status == "RUNNING":
                    break
                if time.time() - start > timeout:
                    raise TimeoutError("Timed out waiting for task to start")
                time.sleep(poll_interval)
        console.print(Panel.fit(Text("Game server has started", style="green"), title="Status"))
