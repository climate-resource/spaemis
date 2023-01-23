import logging

import click

logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """
    Early setup for logging.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=LOGFORMAT,
    )


@click.group()
def cli():
    setup_logging()

