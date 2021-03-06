##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Tests for methods from Reid, Prausnitz and Poling

All methods and parameters from:

The Properties of Gases & Liquids, 4th Edition
Reid, Prausnitz and Polling, 1987, McGraw-Hill

All parameter indicies based on conventions used by the source

Authors: Andrew Lee
"""

import pytest

from pyomo.environ import ConcreteModel, Block, value, Var
from pyomo.common.config import ConfigBlock

from idaes.generic_models.properties.core.pure.RPP import *
from idaes.core.util.misc import add_object_reference


@pytest.fixture()
def frame():
    m = ConcreteModel()

    # Create a dummy parameter block
    m.params = Block()

    m.params.config = ConfigBlock(implicit=True)
    m.params.config.parameter_data = {
        "cp_mol_ig_comp_coeff": {'A': 3.224e1,
                                 'B': 1.924e-3,
                                 'C': 1.055e-5,
                                 'D': -3.596e-9},
        "enth_mol_form_vap_comp_ref": -241.83e3,
        "entr_mol_form_vap_comp_ref": 188.84,
        "pressure_sat_comp_coeff": {'A': -7.76451,
                                    'B': 1.45838,
                                    'C': -2.77580,
                                    'D': -1.23303}}

    # Add necessary parameters to parameter block
    m.params.temperature_ref = Var(initialize=273.15)
    m.params.pressure_ref = Var(initialize=1e5)

    m.params.temperature_crit = Var(initialize=647.3)
    m.params.pressure_crit = Var(initialize=221.2e5)

    # Create a dummy state block
    m.props = Block([1])
    add_object_reference(m.props[1], "params", m.params)

    m.props[1].temperature = Var(initialize=298.15)
    m.props[1].pressure = Var(initialize=101325)

    return m


@pytest.mark.unit
def test_cp_mol_ig_comp(frame):
    cp_mol_ig_comp.build_parameters(frame.params)

    expr = cp_mol_ig_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(33.656, abs=1e-3)

    frame.props[1].temperature.value = 400
    assert value(expr) == pytest.approx(34.467, abs=1e-3)


@pytest.mark.unit
def test_enth_mol_ig_comp(frame):
    enth_mol_ig_comp.build_parameters(frame.params)

    expr = enth_mol_ig_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(-240990.825, abs=1e-3)

    frame.props[1].temperature.value = 400
    assert value(expr) == pytest.approx(-237522.824, abs=1e-3)


@pytest.mark.unit
def test_entr_mol_ig_comp(frame):
    entr_mol_ig_comp.build_parameters(frame.params)

    expr = entr_mol_ig_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(191.780, abs=1e-3)

    frame.props[1].temperature.value = 400
    assert value(expr) == pytest.approx(201.780, abs=1e-3)


@pytest.mark.unit
def test_pressure_sat_comp(frame):
    pressure_sat_comp.build_parameters(frame.params)

    expr = pressure_sat_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(3171.4391, abs=1e-3)

    frame.props[1].temperature.value = 373.15
    assert value(expr) == pytest.approx(101378, rel=1e-4)


@pytest.mark.unit
def test_pressure_sat_comp_dT(frame):
    pressure_sat_comp.build_parameters(frame.params)

    expr = pressure_sat_comp.dT_expression(
            frame.props[1], frame.params, frame.props[1].temperature)

    delta = 1e-4
    val = pressure_sat_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    val_p = pressure_sat_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature+delta)

    dPdT = value((val-val_p)/-delta)

    assert value(expr) == pytest.approx(dPdT, 1e-4)

    frame.props[1].temperature.value = 373.15

    val = pressure_sat_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    val_p = pressure_sat_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature+delta)

    dPdT = value((val-val_p)/-delta)

    assert value(expr) == pytest.approx(dPdT, 1e-4)
