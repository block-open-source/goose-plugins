import click
from goose_plugins.utils.log_streamer import start_log_stream

@click.group()
def cli():
    pass

@cli.command()
def stream_log():
    """Stream the current Goose session log in real-time."""
    click.echo("Starting log stream for the current Goose session...")
    start_log_stream()

if __name__ == '__main__':
    cli()