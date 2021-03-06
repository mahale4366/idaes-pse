﻿Components
==========

The purpose of this section of the documentation is to provide a general introduction to the top
level components of the IDAES Computational Platform. Each component is described in greater 
detail with a link in their description.

.. note::
    IDAES is based on python-based algebraic modeling language, Pyomo. The documentation for 
    its components (i.e. Sets, Parameters, Varirables, Objectives, Constraints, Expressions, and 
    Suffixes) are provided in the 
    `Pyomo documentation <https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/index.html>`_.

.. toctree::
    :maxdepth: 1
    
    flowsheet/index
    property_package/index
    unit_model/index
    dmf/index

.. rubric:: Flowsheet

:ref:`Flowsheet models<user_guide/components/flowsheet/index:Flowsheet>`
are the top level of the IDAES modeling framework. Flowsheet models represent 
traditional process flowsheets, containing a number of unit models connected together into a 
flow network and the property packages.

.. rubric:: Property Package

:ref:`Property packages<user_guide/components/property_package/index:Property Package>` are a 
collection of related models that represent the physical, thermodynamic, and reactive 
properties of the process streams on the IDAES platform.

.. rubric:: Unit Model

:ref:`Unit models<user_guide/components/unit_model/index:Unit Model>` 
represent individual pieces of equipment and their processes on the IDAES platform.

.. rubric:: Data Management Framework

The :ref:`Data Management Framework <user_guide/components/dmf/index:Data Management Framework>`
is used to manage all the data needed by the IDAES framework, including flowsheets, models, 
and results. It stores metadata and data in persistent storage.
