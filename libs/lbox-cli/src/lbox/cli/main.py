import click
import tinydb
from pathlib import Path


@click.group()
def cli():
    db = tinydb.TinyDB(
        Path.home() / "~/.lbox/db.json", create_dirs=True, access_mode="r+"
    )
    print(db.count())


@cli.group()
def key():
    pass


@key.command()
def select():
    print("select")


def init():
    return "init"
