Defining Reaction Packages
==========================

.. contents:: Contents 
    :depth: 2

Introduction
------------

In order to create and use a property package using the IDAES Generic Reaction Package Framework, users must provide a definition for the system they wish to model. The framework supports two approaches for defining the property package, which are described below, both of which are equivalent in practice.

Config Dictionary
-----------------

The most common way to use the Generic Reaction Package Framework is to create an instance of the `GenericReactionParameterBlock` component and provide it with a dictionary of configuration arguments, as shown below:

.. code-block:: python

    m = ConcreteModel()

    m.fs = FlowsheetBlock()

    m.fs.thermo_properties = PhysicalParameterBlock()

    m.fs.reaction_properties = GenericReactionParameterBlock(default={"property_package": m.fs.thermo_properties, config_dict})

In the above example, the PhysicalParameterBlock object can be from any thermophysical property package suitable for the user's application.

Users need to populate `config_dict` with the desired options for their system as described in the other parts of this documentation. An example of a configuration dictionary can be found later on this page. For details on each configuration option, please see the relevant documentation.

Linking to a Thermophysical Property Package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As state information is defined by thermophysical property packages in IDAES, each reaction package must be linked to an appropriate thermophysical property package. This linkage is used by the reaction package to find the state information required to calculate the reaction properties, and thus the thermophysical property package must support all the properties required by the reaction package.

Setting Reaction Basis
^^^^^^^^^^^^^^^^^^^^^^

Many reaction properties (e.g. reaction rates) can be defined on different bases, such as a mass or molar basis. All properties within a package must use the same basis, which can be set using the "reaction_basis" configuration argument (see below). This must be done using the MaterialFlowBasis `Enum`, which can be imported from `idaes.core`.

Configuration Example
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from from idaes.core import MaterialFlowBasis

    config_dict = {
        "reaction_basis": MaterialFlowBasis.molar,
        "rate_reactions": {
            "r1": {"stoichiometry": {("phase_1", "component_1"): -1,
                                     ("phase_1", "component_2"): 2},
                   "heat_of_reaction": constant_dh_rxn,
                   "rate_constant": arrhenius,
                   "rate_form": mole_frac_power_law_rate,
                   "parameter_data": {
                       "dh_rxn_ref": -10000,
                       "arrhenius_const": 1,
                       "energy_activation": 1000}}},
        "equilibrium_reactions": {
            "e1": {"stoichiometry": {("phase_2", "component_1"): -3,
                                     ("phase_2", "component_2"): 4},
                   "heat_of_reaction": constant_dh_rxn,
                   "equilibrium_constant": van_t_hoff,
                   "equilibrium_form": mole_frac_power_law_equil,
                   "parameter_data": {
                       "dh_rxn_ref": -20000,
                       "k_eq_ref": 100,
                       "T_eq_ref": 350}}}}

Class Definition
----------------

Alternatively, the IDAES Generic Reaction Package Framework supports defining classes derived from the IDAES `GenericReactionParameterData` class with methods for defining configuration options and parameters.

Users can define two methods which are called automatically when an instance of the property package is created:

1. `configure`, which defines the users selection of sub-models, and
2. `parameters`, which defines the parameters necessary for the selected property methods.

A basic outline of a user defined Reaction Parameter Block is shown below.

.. code-block:: python

    @declare_process_block_class("UserReactionParameterBlock")
    class UserReactionParameterData(GenericReactionParameterData):
        def configure(self):
            # Set configuration options
            self.config.option_1 = value

        def parameters(self):
            # Define parameters
            self.param_1 = Var(index_set, initialize=value)

Users should populate the `configure` and `parameters` methods as discussed below.

Configure
^^^^^^^^^

The 'configure` method is used to assign values to the configuration arguments, using the format `self.config.option_name = value`.

Parameters
^^^^^^^^^^

The `parameters` method is used to construct all the parameters associated with the property calculations and to specify values for these. The list of necessary parameters is based on the configuration options and the selected methods. Each method lists their necessary parameters in their documentation. Users need only define those parameters required by the options they have chosen.

