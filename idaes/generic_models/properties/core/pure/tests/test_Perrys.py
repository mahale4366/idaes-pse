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
Tests for methods from Perry's

All methods and parameters from:

Perry's Chemical Engineers' Handbook, 7th Edition
Perry, Green, Maloney, 1997, McGraw-Hill

All parameter indicies based on conventions used by the source

Authors: Andrew Lee
"""

import pytest

from pyomo.environ import ConcreteModel, Block, value, Var
from pyomo.common.config import ConfigBlock

from idaes.generic_models.properties.core.pure.Perrys import *
from idaes.core.util.misc import add_object_reference


@pytest.fixture()
def frame():
    m = ConcreteModel()

    # Create a dummy parameter block
    m.params = Block()

    m.params.config = ConfigBlock(implicit=True)
    m.params.config.parameter_data = {
        "dens_mol_liq_comp_coeff": {'1': 5.459e3,  # Factor 1e3 for unit conversion
                                    '2': 0.30542,
                                    '3': 647.13,
                                    '4': 0.081},
        "cp_mol_liq_comp_coeff": {'1': 2.7637e+05,
                                  '2': -2.0901e+03,
                                  '3': 8.1250e+00,
                                  '4': -1.4116e-2,
                                  '5': 9.3701e-06},
        "enth_mol_form_liq_comp_ref": -285.83e3,
        "entr_mol_form_liq_comp_ref": 69.95,
        "pressure_sat_comp_coeff": {'A': -7.76451,
                                    'B': 1.45838,
                                    'C': -2.77580,
                                    'D': -1.23303}}

    # Add necessary parameters to parameter block
    m.params.temperature_ref = Var(initialize=273.16)

    # Create a dummy state block
    m.props = Block([1])
    add_object_reference(m.props[1], "params", m.params)

    m.props[1].temperature = Var(initialize=273.16)

    return m


@pytest.mark.unit
def test_cp_mol_liq_comp(frame):
    cp_mol_liq_comp.build_parameters(frame.params)

    expr = cp_mol_liq_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(76.150, rel=1e-3)

    frame.props[1].temperature.value = 533.15
    assert value(expr) == pytest.approx(89.390, rel=1e-3)


@pytest.mark.unit
def test_enth_mol_liq_comp(frame):
    enth_mol_liq_comp.build_parameters(frame.params)

    expr = enth_mol_liq_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == value(
            frame.params.enth_mol_form_liq_comp_ref)

    frame.props[1].temperature.value = 533.15
    assert value(expr) == pytest.approx(-265423, rel=1e-3)


@pytest.mark.unit
def test_entr_mol_liq_comp(frame):
    entr_mol_liq_comp.build_parameters(frame.params)

    expr = entr_mol_liq_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(1270, rel=1e-3)

    frame.props[1].temperature.value = 533.15
    assert value(expr) == pytest.approx(1322, rel=1e-3)


@pytest.mark.unit
def test_dens_mol_liq_comp(frame):
    dens_mol_liq_comp.build_parameters(frame.params)

    expr = dens_mol_liq_comp.return_expression(
        frame.props[1], frame.params, frame.props[1].temperature)
    assert value(expr) == pytest.approx(55.583e3, rel=1e-4)

    frame.props[1].temperature.value = 333.15
    assert value(expr) == pytest.approx(54.703e3, rel=1e-4)
