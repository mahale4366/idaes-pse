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

from pyomo.environ import ConcreteModel, Constraint, Block, Set, Var
from pyomo.common.config import ConfigBlock, ConfigValue

from idaes.generic_models.properties.core.state_definitions.FTPx import \
    define_state, state_initialization, set_metadata
from idaes.core import (MaterialFlowBasis,
                        MaterialBalanceType,
                        EnergyBalanceType)
from idaes.core.util.misc import add_object_reference


@pytest.mark.unit
def test_set_metadata():
    assert set_metadata(None) is None


class Test1PhaseDefinedStateFalseNoBounds(object):
    # Test define_state method with no bounds and defined_State = False
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={}))

        m.params.phase_list = Set(initialize=["a"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3)], ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=False))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        return m

    @pytest.mark.unit
    def test_always_flash(self, frame):
        define_state(frame.props[1])

        assert frame.props[1].always_flash

    @pytest.mark.unit
    def test_vars(self, frame):
        # Check that all necessary variables have been constructed and have
        # the correct values
        assert isinstance(frame.props[1].flow_mol, Var)
        assert frame.props[1].flow_mol.value == 1

        assert isinstance(frame.props[1].mole_frac_comp, Var)
        assert len(frame.props[1].mole_frac_comp) == 3
        for i in frame.props[1].mole_frac_comp:
            assert i in frame.props[1].params.component_list
            assert frame.props[1].mole_frac_comp[i].value == 1/3

        assert isinstance(frame.props[1].pressure, Var)
        assert frame.props[1].pressure.value == 101325

        assert isinstance(frame.props[1].temperature, Var)
        assert frame.props[1].temperature.value == 298.15

        assert isinstance(frame.props[1].flow_mol_phase, Var)
        assert len(frame.props[1].flow_mol_phase) == 1
        for i in frame.props[1].flow_mol_phase:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].flow_mol_phase[i].value == 1

        assert isinstance(frame.props[1].phase_frac, Var)
        assert len(frame.props[1].phase_frac) == 1
        for i in frame.props[1].phase_frac:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].phase_frac[i].value == 1

        assert isinstance(frame.props[1].mole_frac_phase_comp, Var)
        assert len(frame.props[1].mole_frac_phase_comp) == 3
        for i in frame.props[1].mole_frac_phase_comp:
            assert i in [("a", 1), ("a", 2), ("a", 3)]
            assert frame.props[1].mole_frac_phase_comp[i].value == 1/3

    @pytest.mark.unit
    def test_constraints(self, frame):
        # Check that the correct constraints are present
        assert isinstance(frame.props[1].total_flow_balance, Constraint)
        assert len(frame.props[1].total_flow_balance) == 1
        assert str(frame.props[1].total_flow_balance.body) == str(
            frame.props[1].flow_mol -
            frame.props[1].flow_mol_phase[frame.params.phase_list[1]])

        assert isinstance(frame.props[1].component_flow_balances, Constraint)
        assert len(frame.props[1].component_flow_balances) == 3
        for i in frame.props[1].component_flow_balances:
            assert i in frame.props[1].params.component_list
            assert str(frame.props[1].component_flow_balances[i].body) == str(
                frame.props[1].mole_frac_comp[i] -
                frame.props[1].mole_frac_phase_comp[
                        frame.params.phase_list[1], i])

        assert isinstance(frame.props[1].sum_mole_frac_out, Constraint)
        assert len(frame.props[1].sum_mole_frac_out) == 1
        assert str(frame.props[1].sum_mole_frac_out.body) == str(
                sum(frame.props[1].mole_frac_comp[i]
                    for i in frame.props[1].params.component_list))

        assert isinstance(frame.props[1].phase_fraction_constraint, Constraint)
        assert len(frame.props[1].phase_fraction_constraint) == 1
        for i in frame.props[1].phase_fraction_constraint:
            assert i in frame.props[1].params.phase_list
            assert str(frame.props[1].phase_fraction_constraint[i].body) == \
                str(frame.props[1].phase_frac[i])

        @pytest.mark.unit
        def test_state_initialization(self, frame):
            frame.props[1].flow_mol.value = 100
            for j in frame.params.component_list:
                frame.props[1].mole_frac_comp[j].value = 0.8

            state_initialization(frame.props[1])

            for p in frame.params.phase_list:
                assert frame.props[1].flow_mol_phase[p].value == 50

                for j in frame.params.component_list:
                    assert frame.props[1].mole_frac_phase_comp[p, j].value == \
                        0.8


class Test1PhaseDefinedStateTrueWithBounds(object):
    # Test define_state method with no bounds and defined_State = False
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={
                "flow_mol": (0, 200),
                "temperature": (290, 400),
                "pressure": (1e5, 5e5)}))

        m.params.phase_list = Set(initialize=["a"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3)], ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=True))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        return m

    @pytest.mark.unit
    def test_always_flash(self, frame):
        define_state(frame.props[1])

        assert frame.props[1].always_flash

    @pytest.mark.unit
    def test_vars(self, frame):
        # Check that all necessary variables have been constructed and have
        # the correct values
        assert isinstance(frame.props[1].flow_mol, Var)
        assert frame.props[1].flow_mol.value == 100
        assert frame.props[1].flow_mol.lb == 0
        assert frame.props[1].flow_mol.ub == 200

        assert isinstance(frame.props[1].mole_frac_comp, Var)
        assert len(frame.props[1].mole_frac_comp) == 3
        for i in frame.props[1].mole_frac_comp:
            assert i in frame.props[1].params.component_list
            assert frame.props[1].mole_frac_comp[i].value == 1/3

        assert isinstance(frame.props[1].pressure, Var)
        assert frame.props[1].pressure.value == 3e5
        assert frame.props[1].pressure.lb == 1e5
        assert frame.props[1].pressure.ub == 5e5

        assert isinstance(frame.props[1].temperature, Var)
        assert frame.props[1].temperature.value == 345
        assert frame.props[1].temperature.lb == 290
        assert frame.props[1].temperature.ub == 400

        assert isinstance(frame.props[1].flow_mol_phase, Var)
        assert len(frame.props[1].flow_mol_phase) == 1
        for i in frame.props[1].flow_mol_phase:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].flow_mol_phase[i].value == 100
            assert frame.props[1].flow_mol_phase[i].lb == 0
            assert frame.props[1].flow_mol_phase[i].ub == 200

        assert isinstance(frame.props[1].phase_frac, Var)
        assert len(frame.props[1].phase_frac) == 1
        for i in frame.props[1].phase_frac:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].phase_frac[i].value == 1

        assert isinstance(frame.props[1].mole_frac_phase_comp, Var)
        assert len(frame.props[1].mole_frac_phase_comp) == 3
        for i in frame.props[1].mole_frac_phase_comp:
            assert i in [("a", 1), ("a", 2), ("a", 3)]
            assert frame.props[1].mole_frac_phase_comp[i].value == 1/3

    @pytest.mark.unit
    def test_constraints(self, frame):
        # Check that the correct constraints are present
        assert isinstance(frame.props[1].total_flow_balance, Constraint)
        assert len(frame.props[1].total_flow_balance) == 1
        assert str(frame.props[1].total_flow_balance.body) == str(
            frame.props[1].flow_mol -
            frame.props[1].flow_mol_phase[frame.params.phase_list[1]])

        assert isinstance(frame.props[1].component_flow_balances, Constraint)
        assert len(frame.props[1].component_flow_balances) == 3
        for i in frame.props[1].component_flow_balances:
            assert i in frame.props[1].params.component_list
            assert str(frame.props[1].component_flow_balances[i].body) == str(
                frame.props[1].mole_frac_comp[i] -
                frame.props[1].mole_frac_phase_comp[
                        frame.params.phase_list[1], i])

        assert not hasattr(frame.props[1], "sum_mole_frac_out")

        assert isinstance(frame.props[1].phase_fraction_constraint, Constraint)
        assert len(frame.props[1].phase_fraction_constraint) == 1
        for i in frame.props[1].phase_fraction_constraint:
            assert i in frame.props[1].params.phase_list
            assert str(frame.props[1].phase_fraction_constraint[i].body) == \
                str(frame.props[1].phase_frac[i])

        @pytest.mark.unit
        def test_state_initialization(self, frame):
            frame.props[1].flow_mol.value = 100
            for j in frame.params.component_list:
                frame.props[1].mole_frac_comp[j].value = 0.8

            state_initialization(frame.props[1])

            for p in frame.params.phase_list:
                assert frame.props[1].flow_mol_phase[p].value == 50

                for j in frame.params.component_list:
                    assert frame.props[1].mole_frac_phase_comp[p, j].value == \
                        0.8


class Test2PhaseDefinedStateFalseNoBounds(object):
    # Test define_state method with no bounds and defined_State = False
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={}))

        m.params.phase_list = Set(initialize=["a", "b"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3),
                        ("b", 1), ("b", 2), ("b", 3)],
            ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=False))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        return m

    @pytest.mark.unit
    def test_always_flash(self, frame):
        define_state(frame.props[1])

        assert frame.props[1].always_flash

    @pytest.mark.unit
    def test_vars(self, frame):
        # Check that all necessary variables have been constructed and have
        # the correct values
        assert isinstance(frame.props[1].flow_mol, Var)
        assert frame.props[1].flow_mol.value == 1

        assert isinstance(frame.props[1].mole_frac_comp, Var)
        assert len(frame.props[1].mole_frac_comp) == 3
        for i in frame.props[1].mole_frac_comp:
            assert i in frame.props[1].params.component_list
            assert frame.props[1].mole_frac_comp[i].value == 1/3

        assert isinstance(frame.props[1].pressure, Var)
        assert frame.props[1].pressure.value == 101325

        assert isinstance(frame.props[1].temperature, Var)
        assert frame.props[1].temperature.value == 298.15

        assert isinstance(frame.props[1].flow_mol_phase, Var)
        assert len(frame.props[1].flow_mol_phase) == 2
        for i in frame.props[1].flow_mol_phase:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].flow_mol_phase[i].value == 0.5

        assert isinstance(frame.props[1].phase_frac, Var)
        assert len(frame.props[1].phase_frac) == 2
        for i in frame.props[1].phase_frac:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].phase_frac[i].value == 0.5

        assert isinstance(frame.props[1].mole_frac_phase_comp, Var)
        assert len(frame.props[1].mole_frac_phase_comp) == 6
        for i in frame.props[1].mole_frac_phase_comp:
            assert i in [("a", 1), ("a", 2), ("a", 3),
                         ("b", 1), ("b", 2), ("b", 3)]
            assert frame.props[1].mole_frac_phase_comp[i].value == 1/3

    @pytest.mark.unit
    def test_constraints(self, frame):
        # Check that the correct constraints are present
        assert isinstance(frame.props[1].total_flow_balance, Constraint)
        assert len(frame.props[1].total_flow_balance) == 1
        assert str(frame.props[1].total_flow_balance.body) == str(
                sum(frame.props[1].flow_mol_phase[p]
                    for p in frame.props[1].params.phase_list) -
                frame.props[1].flow_mol)

        assert isinstance(frame.props[1].component_flow_balances, Constraint)
        assert len(frame.props[1].component_flow_balances) == 3
        for i in frame.props[1].component_flow_balances:
            assert i in frame.props[1].params.component_list
            assert str(frame.props[1].component_flow_balances[i].body) == str(
                frame.props[1].flow_mol * frame.props[1].mole_frac_comp[i] -
                sum(frame.props[1].flow_mol_phase[p] *
                    frame.props[1].mole_frac_phase_comp[p, i]
                    for p in frame.props[1].params.phase_list))

        assert isinstance(frame.props[1].sum_mole_frac, Constraint)
        assert len(frame.props[1].sum_mole_frac) == 1
        assert str(frame.props[1].sum_mole_frac.body) == str(
                sum(frame.props[1].mole_frac_phase_comp[
                        frame.props[1].params.phase_list[1], i]
                    for i in frame.props[1].params.component_list) -
                sum(frame.props[1].mole_frac_phase_comp[
                        frame.props[1].params.phase_list[2], i]
                    for i in frame.props[1].params.component_list))

        assert isinstance(frame.props[1].sum_mole_frac_out, Constraint)
        assert len(frame.props[1].sum_mole_frac_out) == 1
        assert str(frame.props[1].sum_mole_frac_out.body) == str(
                sum(frame.props[1].mole_frac_comp[i]
                    for i in frame.props[1].params.component_list))

        assert isinstance(frame.props[1].phase_fraction_constraint, Constraint)
        assert len(frame.props[1].phase_fraction_constraint) == 2
        for i in frame.props[1].phase_fraction_constraint:
            assert i in frame.props[1].params.phase_list
            assert str(frame.props[1].phase_fraction_constraint[i].body) == \
                str(frame.props[1].phase_frac[i]*frame.props[1].flow_mol -
                    frame.props[1].flow_mol_phase[i])

        @pytest.mark.unit
        def test_state_initialization(self, frame):
            frame.props[1].flow_mol.value = 100
            for j in frame.params.component_list:
                frame.props[1].mole_frac_comp[j].value = 0.8

            state_initialization(frame.props[1])

            for p in frame.params.phase_list:
                assert frame.props[1].flow_mol_phase[p].value == 50

                for j in frame.params.component_list:
                    assert frame.props[1].mole_frac_phase_comp[p, j].value == \
                        0.8


class Test2PhaseDefinedStateTrueWithBounds(object):
    # Test define_state method with no bounds and defined_State = False
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={
                "flow_mol": (0, 200),
                "temperature": (290, 400),
                "pressure": (1e5, 5e5)}))

        m.params.phase_list = Set(initialize=["a", "b"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3),
                        ("b", 1), ("b", 2), ("b", 3)],
            ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=True))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        return m

    @pytest.mark.unit
    def test_always_flash(self, frame):
        define_state(frame.props[1])

        assert frame.props[1].always_flash

    @pytest.mark.unit
    def test_vars(self, frame):
        # Check that all necessary variables have been constructed and have
        # the correct values
        assert isinstance(frame.props[1].flow_mol, Var)
        assert frame.props[1].flow_mol.value == 100
        assert frame.props[1].flow_mol.lb == 0
        assert frame.props[1].flow_mol.ub == 200

        assert isinstance(frame.props[1].mole_frac_comp, Var)
        assert len(frame.props[1].mole_frac_comp) == 3
        for i in frame.props[1].mole_frac_comp:
            assert i in frame.props[1].params.component_list
            assert frame.props[1].mole_frac_comp[i].value == 1/3

        assert isinstance(frame.props[1].pressure, Var)
        assert frame.props[1].pressure.value == 3e5
        assert frame.props[1].pressure.lb == 1e5
        assert frame.props[1].pressure.ub == 5e5

        assert isinstance(frame.props[1].temperature, Var)
        assert frame.props[1].temperature.value == 345
        assert frame.props[1].temperature.lb == 290
        assert frame.props[1].temperature.ub == 400

        assert isinstance(frame.props[1].flow_mol_phase, Var)
        assert len(frame.props[1].flow_mol_phase) == 2
        for i in frame.props[1].flow_mol_phase:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].flow_mol_phase[i].value == 50
            assert frame.props[1].flow_mol_phase[i].lb == 0
            assert frame.props[1].flow_mol_phase[i].ub == 200

        assert isinstance(frame.props[1].phase_frac, Var)
        assert len(frame.props[1].phase_frac) == 2
        for i in frame.props[1].phase_frac:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].phase_frac[i].value == 0.5

        assert isinstance(frame.props[1].mole_frac_phase_comp, Var)
        assert len(frame.props[1].mole_frac_phase_comp) == 6
        for i in frame.props[1].mole_frac_phase_comp:
            assert i in [("a", 1), ("a", 2), ("a", 3),
                         ("b", 1), ("b", 2), ("b", 3)]
            assert frame.props[1].mole_frac_phase_comp[i].value == 1/3

    @pytest.mark.unit
    def test_constraints(self, frame):
        # Check that the correct constraints are present
        assert isinstance(frame.props[1].total_flow_balance, Constraint)
        assert len(frame.props[1].total_flow_balance) == 1
        assert str(frame.props[1].total_flow_balance.body) == str(
                sum(frame.props[1].flow_mol_phase[p]
                    for p in frame.props[1].params.phase_list) -
                frame.props[1].flow_mol)

        assert isinstance(frame.props[1].component_flow_balances, Constraint)
        assert len(frame.props[1].component_flow_balances) == 3
        for i in frame.props[1].component_flow_balances:
            assert i in frame.props[1].params.component_list
            assert str(frame.props[1].component_flow_balances[i].body) == str(
                frame.props[1].flow_mol * frame.props[1].mole_frac_comp[i] -
                sum(frame.props[1].flow_mol_phase[p] *
                    frame.props[1].mole_frac_phase_comp[p, i]
                    for p in frame.props[1].params.phase_list))

        assert isinstance(frame.props[1].sum_mole_frac, Constraint)
        assert len(frame.props[1].sum_mole_frac) == 1
        assert str(frame.props[1].sum_mole_frac.body) == str(
                sum(frame.props[1].mole_frac_phase_comp[
                        frame.props[1].params.phase_list[1], i]
                    for i in frame.props[1].params.component_list) -
                sum(frame.props[1].mole_frac_phase_comp[
                        frame.props[1].params.phase_list[2], i]
                    for i in frame.props[1].params.component_list))

        assert not hasattr(frame.props[1], "sum_mole_frac_out")

        assert isinstance(frame.props[1].phase_fraction_constraint, Constraint)
        assert len(frame.props[1].phase_fraction_constraint) == 2
        for i in frame.props[1].phase_fraction_constraint:
            assert i in frame.props[1].params.phase_list
            assert str(frame.props[1].phase_fraction_constraint[i].body) == \
                str(frame.props[1].phase_frac[i]*frame.props[1].flow_mol -
                    frame.props[1].flow_mol_phase[i])

        @pytest.mark.unit
        def test_state_initialization(self, frame):
            frame.props[1].flow_mol.value = 100
            for j in frame.params.component_list:
                frame.props[1].mole_frac_comp[j].value = 0.8

            state_initialization(frame.props[1])

            for p in frame.params.phase_list:
                assert frame.props[1].flow_mol_phase[p].value == 50

                for j in frame.params.component_list:
                    assert frame.props[1].mole_frac_phase_comp[p, j].value == \
                        0.8


class Test3PhaseDefinedStateFalseNoBounds(object):
    # Test define_state method with no bounds and defined_State = False
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={}))

        m.params.phase_list = Set(initialize=["a", "b", "c"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3),
                        ("b", 1), ("b", 2), ("b", 3),
                        ("c", 1), ("c", 2), ("c", 3)],
            ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=False))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        return m

    @pytest.mark.unit
    def test_always_flash(self, frame):
        define_state(frame.props[1])

        assert frame.props[1].always_flash

    @pytest.mark.unit
    def test_vars(self, frame):
        # Check that all necessary variables have been constructed and have
        # the correct values
        assert isinstance(frame.props[1].flow_mol, Var)
        assert frame.props[1].flow_mol.value == 1

        assert isinstance(frame.props[1].mole_frac_comp, Var)
        assert len(frame.props[1].mole_frac_comp) == 3
        for i in frame.props[1].mole_frac_comp:
            assert i in frame.props[1].params.component_list
            assert frame.props[1].mole_frac_comp[i].value == 1/3

        assert isinstance(frame.props[1].pressure, Var)
        assert frame.props[1].pressure.value == 101325

        assert isinstance(frame.props[1].temperature, Var)
        assert frame.props[1].temperature.value == 298.15

        assert isinstance(frame.props[1].flow_mol_phase, Var)
        assert len(frame.props[1].flow_mol_phase) == 3
        for i in frame.props[1].flow_mol_phase:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].flow_mol_phase[i].value == 1/3

        assert isinstance(frame.props[1].phase_frac, Var)
        assert len(frame.props[1].phase_frac) == 3
        for i in frame.props[1].phase_frac:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].phase_frac[i].value == 1/3

        assert isinstance(frame.props[1].mole_frac_phase_comp, Var)
        assert len(frame.props[1].mole_frac_phase_comp) == 9
        for i in frame.props[1].mole_frac_phase_comp:
            assert i in [("a", 1), ("a", 2), ("a", 3),
                         ("b", 1), ("b", 2), ("b", 3),
                         ("c", 1), ("c", 2), ("c", 3)]
            assert frame.props[1].mole_frac_phase_comp[i].value == 1/3

    @pytest.mark.unit
    def test_constraints(self, frame):
        # Check that the correct constraints are present
        assert isinstance(frame.props[1].component_flow_balances, Constraint)
        assert len(frame.props[1].component_flow_balances) == 3
        for j in frame.props[1].component_flow_balances:
            assert j in frame.params.component_list
            assert str(frame.props[1].component_flow_balances[j].body) == str(
                frame.props[1].flow_mol*frame.props[1].mole_frac_comp[j] -
                sum(frame.props[1].flow_mol_phase[p] *
                    frame.props[1].mole_frac_phase_comp[p, j]
                    for p in frame.props[1].params.phase_list))

        assert isinstance(frame.props[1].sum_mole_frac, Constraint)
        assert len(frame.props[1].sum_mole_frac) == 3
        for p in frame.props[1].sum_mole_frac:
            assert p in frame.params.phase_list
            assert str(frame.props[1].sum_mole_frac[p].body) == str(
                    sum(frame.props[1].mole_frac_phase_comp[p, i]
                        for i in frame.props[1].params.component_list))

        assert isinstance(frame.props[1].sum_mole_frac_out, Constraint)
        assert len(frame.props[1].sum_mole_frac_out) == 1
        assert str(frame.props[1].sum_mole_frac_out.body) == str(
                sum(frame.props[1].mole_frac_comp[i]
                    for i in frame.props[1].params.component_list))

        assert isinstance(frame.props[1].phase_fraction_constraint, Constraint)
        assert len(frame.props[1].phase_fraction_constraint) == 3
        for i in frame.props[1].phase_fraction_constraint:
            assert i in frame.props[1].params.phase_list
            assert str(frame.props[1].phase_fraction_constraint[i].body) == \
                str(frame.props[1].phase_frac[i]*frame.props[1].flow_mol -
                    frame.props[1].flow_mol_phase[i])

        @pytest.mark.unit
        def test_state_initialization(self, frame):
            frame.props[1].flow_mol.value = 100
            for j in frame.params.component_list:
                frame.props[1].mole_frac_comp[j].value = 0.8

            state_initialization(frame.props[1])

            for p in frame.params.phase_list:
                assert frame.props[1].flow_mol_phase[p].value == 50

                for j in frame.params.component_list:
                    assert frame.props[1].mole_frac_phase_comp[p, j].value == \
                        0.8


class Test3PhaseDefinedStateTrueWithBounds(object):
    # Test define_state method with no bounds and defined_State = False
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={
                "flow_mol": (0, 200),
                "temperature": (290, 400),
                "pressure": (1e5, 5e5)}))

        m.params.phase_list = Set(initialize=["a", "b", "c"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3),
                        ("b", 1), ("b", 2), ("b", 3),
                        ("c", 1), ("c", 2), ("c", 3)],
            ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=True))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        return m

    @pytest.mark.unit
    def test_always_flash(self, frame):
        define_state(frame.props[1])

        assert frame.props[1].always_flash

    @pytest.mark.unit
    def test_vars(self, frame):
        # Check that all necessary variables have been constructed and have
        # the correct values
        assert isinstance(frame.props[1].flow_mol, Var)
        assert frame.props[1].flow_mol.value == 100
        assert frame.props[1].flow_mol.lb == 0
        assert frame.props[1].flow_mol.ub == 200

        assert isinstance(frame.props[1].mole_frac_comp, Var)
        assert len(frame.props[1].mole_frac_comp) == 3
        for i in frame.props[1].mole_frac_comp:
            assert i in frame.props[1].params.component_list
            assert frame.props[1].mole_frac_comp[i].value == 1/3

        assert isinstance(frame.props[1].pressure, Var)
        assert frame.props[1].pressure.value == 3e5
        assert frame.props[1].pressure.lb == 1e5
        assert frame.props[1].pressure.ub == 5e5

        assert isinstance(frame.props[1].temperature, Var)
        assert frame.props[1].temperature.value == 345
        assert frame.props[1].temperature.lb == 290
        assert frame.props[1].temperature.ub == 400

        assert isinstance(frame.props[1].flow_mol_phase, Var)
        assert len(frame.props[1].flow_mol_phase) == 3
        for i in frame.props[1].flow_mol_phase:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].flow_mol_phase[i].value == 100/3
            assert frame.props[1].flow_mol_phase[i].lb == 0
            assert frame.props[1].flow_mol_phase[i].ub == 200

        assert isinstance(frame.props[1].phase_frac, Var)
        assert len(frame.props[1].phase_frac) == 3
        for i in frame.props[1].phase_frac:
            assert i in frame.props[1].params.phase_list
            assert frame.props[1].phase_frac[i].value == 1/3

        assert isinstance(frame.props[1].mole_frac_phase_comp, Var)
        assert len(frame.props[1].mole_frac_phase_comp) == 9
        for i in frame.props[1].mole_frac_phase_comp:
            assert i in [("a", 1), ("a", 2), ("a", 3),
                         ("b", 1), ("b", 2), ("b", 3),
                         ("c", 1), ("c", 2), ("c", 3)]
            assert frame.props[1].mole_frac_phase_comp[i].value == 1/3

    @pytest.mark.unit
    def test_constraints(self, frame):
        # Check that the correct constraints are present
        assert isinstance(frame.props[1].component_flow_balances, Constraint)
        assert len(frame.props[1].component_flow_balances) == 3
        for j in frame.props[1].component_flow_balances:
            assert j in frame.params.component_list
            assert str(frame.props[1].component_flow_balances[j].body) == str(
                frame.props[1].flow_mol*frame.props[1].mole_frac_comp[j] -
                sum(frame.props[1].flow_mol_phase[p] *
                    frame.props[1].mole_frac_phase_comp[p, j]
                    for p in frame.props[1].params.phase_list))

        assert isinstance(frame.props[1].sum_mole_frac, Constraint)
        assert len(frame.props[1].sum_mole_frac) == 3
        for p in frame.props[1].sum_mole_frac:
            assert p in frame.params.phase_list
            assert str(frame.props[1].sum_mole_frac[p].body) == str(
                    sum(frame.props[1].mole_frac_phase_comp[p, i]
                        for i in frame.props[1].params.component_list))

        assert not hasattr(frame.props[1], "sum_mole_frac_out")

        assert isinstance(frame.props[1].phase_fraction_constraint, Constraint)
        assert len(frame.props[1].phase_fraction_constraint) == 3
        for i in frame.props[1].phase_fraction_constraint:
            assert i in frame.props[1].params.phase_list
            assert str(frame.props[1].phase_fraction_constraint[i].body) == \
                str(frame.props[1].phase_frac[i]*frame.props[1].flow_mol -
                    frame.props[1].flow_mol_phase[i])

        @pytest.mark.unit
        def test_state_initialization(self, frame):
            frame.props[1].flow_mol.value = 100
            for j in frame.params.component_list:
                frame.props[1].mole_frac_comp[j].value = 0.8

            state_initialization(frame.props[1])

            for p in frame.params.phase_list:
                assert frame.props[1].flow_mol_phase[p].value == 50

                for j in frame.params.component_list:
                    assert frame.props[1].mole_frac_phase_comp[p, j].value == \
                        0.8


class TestCommon(object):
    @pytest.fixture(scope="class")
    def frame(self):
        m = ConcreteModel()

        # Create a dummy parameter block
        m.params = Block()

        # Add necessary parameters to parameter block
        m.params.config = ConfigBlock()
        m.params.config.declare("state_bounds", ConfigValue(default={}))

        m.params.phase_list = Set(initialize=["a", "b"], ordered=True)
        m.params.component_list = Set(initialize=[1, 2, 3], ordered=True)
        m.params._phase_component_set = Set(
            initialize=[("a", 1), ("a", 2), ("a", 3),
                        ("b", 1), ("b", 2), ("b", 3)], ordered=True)

        # Create a dummy state block
        m.props = Block([1])
        m.props[1].config = ConfigBlock()
        m.props[1].config.declare("defined_state", ConfigValue(default=False))
        add_object_reference(m.props[1], "params", m.params)

        # Add necessary variables that would be built by other methods
        m.props[1].dens_mol_phase = Var(m.params.phase_list, initialize=1)
        m.props[1].enth_mol_phase = Var(m.params.phase_list, initialize=1)

        define_state(m.props[1])

        return m

    # Test General Methods
    @pytest.mark.unit
    def test_get_material_flow_terms(self, frame):
        for p in frame.params.phase_list:
            for j in frame.params.component_list:
                assert frame.props[1].get_material_flow_terms(p, j) == (
                    frame.props[1].flow_mol_phase[p] *
                    frame.props[1].mole_frac_phase_comp[p, j])

    @pytest.mark.unit
    def test_get_enthalpy_flow_terms(self, frame):
        for p in frame.params.phase_list:
            assert frame.props[1].get_enthalpy_flow_terms(p) == (
                frame.props[1].flow_mol_phase[p] *
                frame.props[1].enth_mol_phase[p])

    @pytest.mark.unit
    def test_get_material_density_terms(self, frame):
        for p in frame.params.phase_list:
            for j in frame.params.component_list:
                assert frame.props[1].get_material_density_terms(p, j) == (
                    frame.props[1].dens_mol_phase[p] *
                    frame.props[1].mole_frac_phase_comp[p, j])

    @pytest.mark.unit
    def test_get_energy_density_terms(self, frame):
        for p in frame.params.phase_list:
            assert frame.props[1].get_energy_density_terms(p) == (
                frame.props[1].dens_mol_phase[p] *
                frame.props[1].enth_mol_phase[p])

    @pytest.mark.unit
    def test_default_material_balance_type(self, frame):
        assert frame.props[1].default_material_balance_type() == \
            MaterialBalanceType.componentTotal

    @pytest.mark.unit
    def test_default_energy_balance_type(self, frame):
        assert frame.props[1].default_energy_balance_type() == \
            EnergyBalanceType.enthalpyTotal

    @pytest.mark.unit
    def test_get_material_flow_basis(self, frame):
        assert frame.props[1].get_material_flow_basis() == \
            MaterialFlowBasis.molar

    @pytest.mark.unit
    def test_define_state_vars(self, frame):
        assert frame.props[1].define_state_vars() == \
            {"flow_mol": frame.props[1].flow_mol,
             "mole_frac_comp": frame.props[1].mole_frac_comp,
             "temperature": frame.props[1].temperature,
             "pressure": frame.props[1].pressure}

    @pytest.mark.unit
    def test_define_port_members(self, frame):
        assert frame.props[1].define_state_vars() == \
            {"flow_mol": frame.props[1].flow_mol,
             "mole_frac_comp": frame.props[1].mole_frac_comp,
             "temperature": frame.props[1].temperature,
             "pressure": frame.props[1].pressure}

    @pytest.mark.unit
    def test_define_display_vars(self, frame):
        assert frame.props[1].define_state_vars() == \
            {"flow_mol": frame.props[1].flow_mol,
             "mole_frac_comp": frame.props[1].mole_frac_comp,
             "temperature": frame.props[1].temperature,
             "pressure": frame.props[1].pressure}
