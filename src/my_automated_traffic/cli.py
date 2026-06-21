"""Command Line Interface (CLI) orchestrator for the Affiliate Strategy suite."""

import click
from my_automated_traffic.database import DatabaseManager

@click.group()
@click.option('--db-path', default='campaigns.db', help='Path to SQLite database')
@click.pass_context
def main_cli(ctx: click.Context, db_path: str) -> None:
    """Main command line entry point for the campaign orchestrator.

    Args:
        ctx: The Click context object.
        db_path: Path to the SQLite campaign database.
    """
    ctx.ensure_object(dict)
    ctx.obj['db'] = DatabaseManager(db_path)
    ctx.obj['db'].initialize()

@main_cli.command()
@click.option('--url', required=True, help='URL of the affiliate offer')
@click.option('--desc', default='', help='Description of the affiliate offer')
@click.option('--rules', default='', help='Compliance/promotional rules')
@click.option('--niche', required=True, help='Target niche for the offer')
@click.pass_context
def add_offer(ctx: click.Context, url: str, desc: str, rules: str, niche: str) -> None:
    """Add a new affiliate offer to the database.

    Args:
        ctx: The Click context object.
        url: The affiliate offer URL.
        desc: Description of the offer.
        rules: Compliance guidelines or rules.
        niche: Niche for the offer.
    """
    db: DatabaseManager = ctx.obj['db']
    offer_id = db.add_offer(url, desc, rules, niche)
    click.echo(f"Successfully added offer with ID: {offer_id}")

if __name__ == '__main__':
    main_cli(obj={})
