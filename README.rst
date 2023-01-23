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

If you also want to run the example notebooks install additional
dependencies using

.. code:: bash

    pip install spaemis[notebooks]

In order to run the example configurations, the `SSP database <https://tntcat.iiasa.ac.at/SspDb/dsd?Action=htmlpage&page=about>`_
must be downloaded manually. This requires the creation of an account and the acceptance of
the terms of use of the dataset. Specifically, the `SSP_IAM_V2_201811.csv` and `SSP_CMIP6_201811.csv` files should be
copied to `data/raw/`.


Developer Installation
======================

.. code:: bash

    make -B virtual-environment


.. sec-end-installation

Documentation
-------------

**Still to write and deploy**

Documentation can be found at our `documentation pages <https://spaemis.readthedocs.io/en/latest/>`_
(we are thankful to `Read the Docs <https://readthedocs.org/>`_ for hosting us).

Contributing
------------

Please see the `Development section of the docs <https://h2-adjust.readthedocs.io/en/latest/development.html>`_.