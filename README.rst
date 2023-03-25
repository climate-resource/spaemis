Spatial Emissions
=================

Brief summary
+++++++++++++

.. sec-begin-long-description
.. sec-begin-index

``spaemis`` is a tool for producing a coherent set of emissions projections for regional
air quality modelling.


This model is a work in progress and is under active development. This work was undertaken
by `Climate Resource <https://www.climate-resource.com>`_ and funded by `CSIRO <https://www.csiro.au/en/>`_

.. sec-end-index

License
-------

.. sec-begin-license

spaemis is free software under a MIT License, see
`LICENSE <https://github.com/climate-resource/spaemis/blob/master/LICENSE>`_.

.. sec-end-license
.. sec-end-long-description

.. sec-begin-installation

Installation
------------

spaemis can be installed with pip

.. code:: bash

    # Not currently working
    pip install spaemis

If you also want to be able to generate set of results install additional notebook-related
dependencies using

.. code:: bash

    pip install spaemis[notebooks]

A set of `Input4MIPs <https://esgf-node.llnl.gov/projects/input4mips/>`_ emissions data
are also required for the scenarios to run. Alternatively, `h2-adjust <https://github.com/climate-resource/h2-adjust>`_
can be used to generate an emission scenario which has been adjusted to better represent
the expected emissions associated with the future hydrogen economy.


Developer Installation
++++++++++++++++++++++

This repository uses Git LFS for managing some of the larger NetCDF files. Follow the
`installation instructions <https://git-lfs.com/>`_ for Git LFS before working with the
code.

After Git LFS has been installed, a virtual environment can be created to which the
development dependencies for ``spaemis`` are installed:

.. code:: bash


    make -B virtual-environment


.. sec-end-installation

Documentation
-------------

** Still to write and deploy **


Contributing
------------

Please see the `Development section of the docs <https://spaemis.readthedocs.io/en/latest/development.html>`_.