"""
Run notebooks in an isolated fashion
"""

import logging
import os.path
from collections.abc import Iterable
from typing import Any

import jupytext
import papermill as pm

from spaemis import __version__
from spaemis.config import DownscalingScenarioConfig, converter, get_path, load_config
from spaemis.constants import ROOT_DIR

logger = logging.getLogger(__name__)


def run_notebooks(
    notebooks: Iterable[str],
    output_dir,
    parameters: dict[str, Any],
    notebook_dir=os.path.join(ROOT_DIR, "notebooks"),
) -> None:
    """
    Run a set of notebooks

    Each notebook is copied to the output directory (suffix '-template.ipynb') before
    being run by papermill ('.ipynb') with a set of parameters.

    Parameters
    ----------
    notebooks
        Notebooks to run

        Each item should be the filename of a notebook in ``notebook_dir`` without the
        file extension (``.ipynb``)
    output_dir
        Directory to write results to
    parameters
        Parameters to pass to the notebook using ``papermill``
    notebook_dir
        Directory containing the notebooks

    Raises
    ------
    NotebookException
        Something has gone wrong when running the notebook.

        The state of the notebook when it failed is written to the ``output_dir``
    """
    for nb in notebooks:
        input_fname = os.path.join(notebook_dir, nb + ".py")
        output_template_fname = os.path.join(output_dir, nb + "-template.ipynb")

        logger.info(f"Writing template notebook: {output_template_fname}")
        notebook_jupytext = jupytext.read(input_fname)
        try:
            jupytext.write(
                notebook_jupytext,
                output_template_fname,
                fmt="ipynb",
            )
            pm.execute_notebook(
                output_template_fname,
                os.path.join(output_dir, nb + ".ipynb"),
                parameters=parameters,
            )
        except Exception as e:
            raise NotebookException(e, nb) from e


class NotebookException(Exception):
    """
    An exception occurred when running a notebook
    """

    def __init__(self, exc, filename):
        self.exc = exc
        self.filename = filename
        super().__init__(self.exc)

    def __str__(self):
        return f"{self.filename} failed to execute: {self.exc}"


class NotebookRunner:
    """
    Manage the running of a set of notebooks

    This creates the require directories and passing configuration ot the notebook
    """

    def __init__(self, config_path: str, output_path: str) -> None:
        logger.info(f"Starting spaemis {__version__}")

        self.config = load_config(config_path)
        self.config_path = str(config_path)
        self.output_path = str(output_path)

        if not output_path:
            raise ValueError("No value for output_dir specified")

    def create_output_directory(self) -> None:
        """
        Create output directories for the current run

        This creates the following directories under the targeted output directory:

        * inputs
        * notebooks
        * outputs
        * plots

        Additionally, the configuration for the current run is written to ``inputs``
        directory.
        """
        if os.path.exists(self.output_path):
            raise ValueError(
                f"Output directory {self.output_path} already exists. "
                "Please select a new output directory or remove the existing directory"
            )

        os.makedirs(self.output_path)

        os.makedirs(os.path.join(self.output_path, "inputs"))
        os.makedirs(os.path.join(self.output_path, "notebooks"))
        os.makedirs(os.path.join(self.output_path, "outputs"))
        os.makedirs(os.path.join(self.output_path, "plots"))

        # Copy out the desired config
        updated_config_fname = os.path.join(
            get_path(self.output_path, "inputs"), "config.yaml"
        )
        with open(updated_config_fname, "w") as fh:
            fh.write(converter.dumps(self.config, DownscalingScenarioConfig))
        # Update the config path to use the new one
        self.config_path = updated_config_fname

    def run(self, notebooks: Iterable[str]) -> None:
        """
        Run a set of notebooks
        """
        # Run the various notebooks
        run_notebooks(
            notebooks,
            get_path(self.output_path, "notebooks"),
            parameters={
                "CONFIG_PATH": self.config_path,
                "RESULTS_PATH": self.output_path,
            },
        )
