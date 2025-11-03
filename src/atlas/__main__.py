"""Command-line interface."""

import typer


app: typer.Typer = typer.Typer()


@app.command(name="atlas")
def main() -> None:
    """Atlas."""


if __name__ == "__main__":
    app()  # pragma: no cover
