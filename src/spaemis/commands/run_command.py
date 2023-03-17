import logging
import os.path
import shutil

import click

from spaemis.commands.base import cli
from spaemis.config import get_default_results_dir
from spaemis.notebooks import NotebookRunner

logger = logging.getLogger(__name__)


@cli.command(name="run")
@click.option(
    "-c", "--config", help="Configuration file to run", type=click.Path(exists=True)
)
@click.option(
    "-o",
    "--output-dir",
    help="Output directory",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Removes any existing results before running",
)
def run_command(config, output_dir, force):
    if output_dir is None:
        output_dir = get_default_results_dir(config)
        logger.warning(f"No output directory specified. Defaulting to {output_dir}")

    if os.path.exists(output_dir):
        if force:
            logger.warning("Removing existing results")
            shutil.rmtree(output_dir)
        else:
            raise click.ClickException(
                f"Directory {output_dir} already exists. Either remove or run with '--force'"
            )

    results = NotebookRunner(config, output_dir)
    results.create_output_directory()

    notebooks_to_run = (
        "100_copy_inputs",
        "200_run_victoria",
        # "300_run_australia",
    )

    results.run(notebooks_to_run)
