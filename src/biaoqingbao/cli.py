import click
from waitress import serve

from .factory import create_app
from .models import db
from .version import __version__


@click.group()
@click.version_option(__version__)
def cli():
    """biaoqingbao cli."""


@cli.command()
def create_table():
    """Initialize sqlite database file."""
    app = create_app()
    with app.app_context():
        db.create_all()


@cli.command()
def drop_all():
    """Drop all database tables."""
    app = create_app()
    with app.app_context():
        db.drop_all()


@cli.command("run")
@click.option("--port", default=5000, help="Network port to listen to.")
def run(port: int):
    """Run biaoqingbao server."""
    app = create_app()
    serve(app, host="127.0.0.1", port=port)
