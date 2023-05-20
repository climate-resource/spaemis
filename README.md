# SpaEmis

<!--- sec-begin-description -->

Produce a coherent set of emissions for regional air quality modelling


This model is a work in progress and is under active development. This work was undertaken
by `Climate Resource <https://www.climate-resource.com>`_ and funded by `CSIRO <https://www.csiro.au/en/>`_
<!--- sec-end-description -->

## Installation

<!--- sec-begin-installation -->

Spaemis can be installed with pip:

```bash
pip install spaemis
```

Additional dependencies can be installed using

```bash
# To add plotting dependencies
pip install spaemis[plots]
# To add notebook dependencies
pip install spaemis[notebooks]
```

A set of `Input4MIPs <https://esgf-node.llnl.gov/projects/input4mips/>`_ emissions data
is also required as it is a common proxy.

<!--- sec-end-installation -->

<!--- sec-begin-installation-dev -->

### For developers

For development, we rely on [poetry](https://python-poetry.org) for all our
dependency management. To get started, you will need to make sure that poetry
is installed
(https://python-poetry.org/docs/#installing-with-the-official-installer, we
found that pipx and pip worked better to install on a Mac).

For all of work, we use our `Makefile`.
You can read the instructions out and run the commands by hand if you wish,
but we generally discourage this because it can be error prone.
In order to create your environment, run `make virtual-environment`.

If there are any issues, the messages from the `Makefile` should guide you
through. If not, please raise an issue in the [issue tracker][issue tracker].

<!--- sec-end-installation-dev -->

<!--- sec-begin-links -->

[issue tracker]: https://github.com/climate-resource/spaemis/issues

<!--- sec-end-links -->
