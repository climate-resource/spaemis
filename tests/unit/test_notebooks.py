import os

import pytest

from spaemis.config import load_config
from spaemis.constants import ROOT_DIR
from spaemis.notebooks import NotebookException, NotebookRunner, run_notebooks


@pytest.fixture()
def nb_runner(tmpdir, config_file):
    return NotebookRunner(config_file, tmpdir / "out")


class TestNotebookRunner:
    def test_missing(self, config_file):
        with pytest.raises(FileNotFoundError, match="No such file or directory: ''"):
            NotebookRunner("", "")

        with pytest.raises(ValueError, match="No value for output_dir specified"):
            NotebookRunner(config_file, None)

        with pytest.raises(ValueError, match="No value for output_dir specified"):
            NotebookRunner(config_file, "")

    def test_create_output_dir(self, nb_runner, tmpdir, config, config_file):
        assert nb_runner.config_path == config_file
        nb_runner.create_output_directory()

        assert (tmpdir / "out" / "inputs/config.yaml").exists()
        assert (tmpdir / "out" / "notebooks").exists()
        assert (tmpdir / "out" / "outputs").exists()
        assert (tmpdir / "out" / "plots").exists()

        # Check that the configuration can be read back
        cfg = load_config(tmpdir / "out" / "inputs/config.yaml")
        assert cfg == config

        assert nb_runner.config_path == str(tmpdir / "out" / "inputs" / "config.yaml")

    def test_create_already_exists(self, nb_runner, tmpdir):
        os.makedirs(tmpdir / "out")

        with pytest.raises(
            ValueError,
            match=f"Output directory {nb_runner.output_path} already exists. ",
        ):
            nb_runner.create_output_directory()

    def test_run(self, nb_runner, mocker, tmpdir):
        notebooks = ["nb1.ipynb"]
        mock_run = mocker.patch("spaemis.notebooks.run_notebooks")

        nb_runner.create_output_directory()
        nb_runner.run(notebooks)

        mock_run.assert_called_once_with(
            notebooks,
            str(tmpdir / "out" / "notebooks"),
            parameters={
                "CONFIG_PATH": str(tmpdir / "out" / "inputs" / "config.yaml"),
                "RESULTS_PATH": str(tmpdir / "out"),
            },
        )


def test_run_notebooks(mocker):
    params = {"test": "example"}

    mock_jupytext = mocker.patch("spaemis.notebooks.jupytext")
    mock_papermill = mocker.patch("spaemis.notebooks.pm")

    run_notebooks(
        # Note no .ipynb
        ["example"],
        "out-dir",
        params,
    )

    exp_input_path = os.path.join(ROOT_DIR, "notebooks", "example.ipynb")
    exp_template_path = os.path.join("out-dir", "example-template.ipynb")
    exp_output_path = os.path.join("out-dir", "example.ipynb")

    mock_jupytext.write.assert_called_once_with(
        mock_jupytext.read(exp_input_path), exp_template_path, fmt="ipynb"
    )
    mock_papermill.execute_notebook.assert_called_once_with(
        exp_template_path, exp_output_path, parameters=params
    )


def test_run_notebook_failed(mocker):
    mock_jupytext = mocker.patch("spaemis.notebooks.jupytext")
    mock_jupytext.write.side_effect = ValueError("something went wrong")

    with pytest.raises(NotebookException) as excinfo:
        run_notebooks(
            ["example", "other"],
            "out-dir",
            {},
        )

    assert excinfo.value.filename == "example"
    assert str(excinfo.value).startswith(
        "example failed to execute: something went wrong"
    )
