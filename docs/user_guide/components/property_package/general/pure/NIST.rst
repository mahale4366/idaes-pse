NIST Webbook
============

.. contents:: Contents 
    :depth: 2

Source
------

Pure component properties as used by the NIST WebBook, `<https://webbook.nist.gov/chemistry/>`_ Retrieved: September 13th, 2019

Ideal Gas Molar Heat Capacity (Constant Pressure)
-------------------------------------------------

NIST uses the Shomate equation for the ideal gas molar heat capacity, which is shown below:

.. math:: c_{\text{p ig}} = A + B \times t + C \times t^2 + D \times t^3 + \frac{E}{t^2}

where :math:`t = \frac{T}{1000}`.

**Parameters**

.. csv-table::
   :header: "Symbol", "Parameter Name", "Indices", "Description"

   ":math:`A, B, C, D, E, F, G, H`", "cp_mol_ig_comp_coeff", "`['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']`", ""

.. note::
    The parameter `cp_mol_ig_comp_coeff` is also used when calculating specific enthalpy and entropy and parameters 'F', 'G' and 'H' are only required for these properties.

Ideal Gas Molar Enthalpy
------------------------

The correlation for the ideal gas molar enthalpy is derived from the correlation for the molar heat capacity and is given below:

.. math:: \frac{h_{\text{ig}} - h_{\text{ig ref}}}{1000} = A \times (t-t_{ref}) + \frac{B}{2} \times (t^2 - t_{ref}^2) + \frac{C}{3} \times (t^3 - t_{ref}^3) + \frac{D}{4} \times (t^4 - t_{ref}^4) + E \times (\frac{1}{t} - \frac{1}{t_{ref}}) + F - H

.. csv-table::
   :header: "Symbol", "Parameter Name", "Indices", "Description"

   ":math:`A, B, C, D, E, F, G, H`", "cp_mol_ig_comp_coeff", "`['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']`", ""

.. note::
    This correlation uses the same parameters as for the ideal gas heat capacity with additional parameters `F` and `H`. These parameters account for the enthalpy at the reference state defined by NIST. Users wanting to use a different reference state will need to update `H`.

Ideal Gas Molar Entropy
------------------------

The correlation for the ideal gas molar entropy is derived from the correlation for the molar heat capacity and is given below:

.. math:: s_{\text{ig}} = A \times ln(t) + B \times t + \frac{C}{2} \times t^2 + \frac{D}{3} \times t^3 + \frac{E}{2 \times t^2} + G 

**Parameters**

.. csv-table::
   :header: "Symbol", "Parameter Name", "Indices", "Description"

   ":math:`A, B, C, D, E, F, G, H`", "cp_mol_ig_comp_coeff", "`['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']`", ""

.. note::
    This correlation uses the same parameters as for the ideal gas heat capacity with additional parameter `G`, which accounts for the standard entropy at the reference state defined by NIST. Users wanting to use a different reference state will need to update `G`. 

Saturation (Vapor) Pressure
---------------------------

NIST uses the Antoine equation to calculate the vapor pressure of a component, which is given below:

.. math:: log_{10}(P_{sat}) = A - \frac{B}{T+C}

**Parameters**

.. csv-table::
   :header: "Symbol", "Parameter Name", "Indices", "Description"

   ":math:`A, B, C`", "pressure_sat_comp_coeff", "`['A', 'B', 'C']`", ""

.. note::
    The Antoine equation is generally written with saturation pressure expressed in bars. The units of the correlation can be converted to Pascals by adding 5 to :math:`A`.
