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
Tests for 0D heat exchanger models.

Author: John Eslick
"""
import pytest

from pyomo.environ import (ConcreteModel,
                           Constraint,
                           Expression,
                           TerminationCondition,
                           SolverStatus,
                           value,
                           Var)
from pyomo.common.config import ConfigBlock

from idaes.core import (FlowsheetBlock,
                        MaterialBalanceType,
                        EnergyBalanceType,
                        MomentumBalanceType)
from idaes.generic_models.unit_models.heat_exchanger import (delta_temperature_lmtd_callback,
                                              HeatExchanger,
                                              HeatExchangerFlowPattern)

from idaes.generic_models.properties.activity_coeff_models.BTX_activity_coeff_VLE \
    import BTXParameterBlock
from idaes.generic_models.properties import iapws95
from idaes.generic_models.properties.examples.saponification_thermo import \
    SaponificationParameterBlock

from idaes.core.util.model_statistics import (degrees_of_freedom,
                                              number_variables,
                                              number_total_constraints,
                                              fixed_variables_set,
                                              activated_constraints_set,
                                              number_unused_variables)
from idaes.core.util.testing import (get_default_solver,
                                     PhysicalParameterTestBlock,
                                     initialization_tester)
from pyomo.util.calc_var_value import calculate_variable_from_constraint


# -----------------------------------------------------------------------------
# Get default solver for testing
solver = get_default_solver()


# -----------------------------------------------------------------------------
@pytest.mark.unit
def test_bad_option():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    with pytest.raises(KeyError):
        m.fs.unit = HeatExchanger(default={"I'm a bad option": "hot"})


@pytest.mark.unit
def test_same_name():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    with pytest.raises(NameError):
        m.fs.unit = HeatExchanger(default={"cold_side_name": "shell"})


@pytest.mark.unit
def test_config():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})

    m.fs.properties = PhysicalParameterTestBlock()

    m.fs.unit = HeatExchanger(default={
        "shell": {"property_package": m.fs.properties},
        "tube": {"property_package": m.fs.properties}})

    # Check unit config arguments
    # There are 8 to 10 arguments since you can add a side 1 and 2 config by
    # side_1, side_2, or whatever the user named them
    assert len(m.fs.unit.config) >= 8 and len(m.fs.unit.config) <= 10

    assert not m.fs.unit.config.dynamic
    assert not m.fs.unit.config.has_holdup
    assert isinstance(m.fs.unit.config.shell, ConfigBlock)
    assert isinstance(m.fs.unit.config.tube, ConfigBlock)
    assert m.fs.unit.config.delta_temperature_callback is \
        delta_temperature_lmtd_callback
    assert m.fs.unit.config.flow_pattern == \
        HeatExchangerFlowPattern.countercurrent

    # Check shell config
    assert len(m.fs.unit.config.shell) == 7
    assert m.fs.unit.config.shell.material_balance_type == \
        MaterialBalanceType.useDefault
    assert m.fs.unit.config.shell.energy_balance_type == \
        EnergyBalanceType.useDefault
    assert m.fs.unit.config.shell.momentum_balance_type == \
        MomentumBalanceType.pressureTotal
    assert not m.fs.unit.config.shell.has_phase_equilibrium
    assert not m.fs.unit.config.shell.has_pressure_change
    assert m.fs.unit.config.shell.property_package is m.fs.properties

    # Check tube config
    assert len(m.fs.unit.config.tube) == 7
    assert m.fs.unit.config.tube.material_balance_type == \
        MaterialBalanceType.useDefault
    assert m.fs.unit.config.tube.energy_balance_type == \
        EnergyBalanceType.useDefault
    assert m.fs.unit.config.tube.momentum_balance_type == \
        MomentumBalanceType.pressureTotal
    assert not m.fs.unit.config.tube.has_phase_equilibrium
    assert not m.fs.unit.config.tube.has_pressure_change
    assert m.fs.unit.config.tube.property_package is m.fs.properties

@pytest.mark.skipif(not iapws95.iapws95_available(),
                    reason="IAPWS not available")
@pytest.mark.skipif(solver is None, reason="Solver not available")
@pytest.mark.unit
def test_costing():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})

    m.fs.properties = iapws95.Iapws95ParameterBlock()

    m.fs.unit = HeatExchanger(default={
                "shell": {"property_package": m.fs.properties},
                "tube": {"property_package": m.fs.properties},
                "flow_pattern": HeatExchangerFlowPattern.countercurrent})
#   Set inputs
    m.fs.unit.inlet_1.flow_mol[0].fix(100)
    m.fs.unit.inlet_1.enth_mol[0].fix(4000)
    m.fs.unit.inlet_1.pressure[0].fix(101325)

    m.fs.unit.inlet_2.flow_mol[0].fix(100)
    m.fs.unit.inlet_2.enth_mol[0].fix(3500)
    m.fs.unit.inlet_2.pressure[0].fix(101325)

    m.fs.unit.area.fix(1000)
    m.fs.unit.overall_heat_transfer_coefficient.fix(100)

    assert degrees_of_freedom(m) == 0

    m.fs.unit.initialize()

    m.fs.unit.get_costing()
    calculate_variable_from_constraint(
                m.fs.unit.costing.base_cost,
                m.fs.unit.costing.base_cost_eq)

    calculate_variable_from_constraint(
                m.fs.unit.costing.purchase_cost,
                m.fs.unit.costing.cp_cost_eq)

    results = solver.solve(m)
    assert m.fs.unit.costing.purchase_cost.value == \
                                            pytest.approx(529738.6793, 1e-5)


@pytest.mark.unit
def test_costing_book():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    m.fs.properties = iapws95.Iapws95ParameterBlock()
    m.fs.unit = HeatExchanger(default={
                "shell": {"property_package": m.fs.properties},
                "tube": {"property_package": m.fs.properties},
                "flow_pattern": HeatExchangerFlowPattern.countercurrent})
    #   Set inputs
    m.fs.unit.inlet_1.flow_mol[0].fix(100)
    m.fs.unit.inlet_1.enth_mol[0].fix(4000)
    m.fs.unit.inlet_1.pressure[0].fix(101325)

    m.fs.unit.inlet_2.flow_mol[0].fix(100)
    m.fs.unit.inlet_2.enth_mol[0].fix(3500)
    m.fs.unit.inlet_2.pressure[0].fix(101325)

    m.fs.unit.area.fix(1000)
    m.fs.unit.overall_heat_transfer_coefficient.fix(100)
    # costing
    m.fs.unit.get_costing(hx_type='floating_head', length_factor='20ft',
                          year='2018')
    m.fs.unit.area.fix(669.738)  # m2
    m.fs.unit.costing.pressure_factor.fix(1.19)
    m.fs.unit.costing.material_factor.fix(4.05)
    m.fs.costing.CE_index = 550
    m.fs.unit.costing.hx_os = 1.0
    calculate_variable_from_constraint(
            m.fs.unit.costing.base_cost,
            m.fs.unit.costing.base_cost_eq)

    calculate_variable_from_constraint(
            m.fs.unit.costing.purchase_cost,
            m.fs.unit.costing.cp_cost_eq)

    assert m.fs.unit.costing.base_cost.value == \
        pytest.approx(78802.0518, 1e-5)
    assert m.fs.unit.costing.purchase_cost.value == \
        pytest.approx(417765.1377, 1e-5)


# -----------------------------------------------------------------------------
class TestBTX_cocurrent(object):
    @pytest.fixture(scope="class")
    def btx(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = BTXParameterBlock(default={"valid_phase": 'Liq'})

        m.fs.unit = HeatExchanger(default={
                "shell": {"property_package": m.fs.properties},
                "tube": {"property_package": m.fs.properties},
                "flow_pattern": HeatExchangerFlowPattern.cocurrent})

        return m

    @pytest.mark.build
    @pytest.mark.unit
    def test_build(self, btx):
        assert hasattr(btx.fs.unit, "inlet_1")
        assert len(btx.fs.unit.inlet_1.vars) == 4
        assert hasattr(btx.fs.unit.inlet_1, "flow_mol")
        assert hasattr(btx.fs.unit.inlet_1, "mole_frac_comp")
        assert hasattr(btx.fs.unit.inlet_1, "temperature")
        assert hasattr(btx.fs.unit.inlet_1, "pressure")

        assert hasattr(btx.fs.unit, "inlet_2")
        assert len(btx.fs.unit.inlet_2.vars) == 4
        assert hasattr(btx.fs.unit.inlet_2, "flow_mol")
        assert hasattr(btx.fs.unit.inlet_2, "mole_frac_comp")
        assert hasattr(btx.fs.unit.inlet_2, "temperature")
        assert hasattr(btx.fs.unit.inlet_2, "pressure")

        assert hasattr(btx.fs.unit, "outlet_1")
        assert len(btx.fs.unit.outlet_1.vars) == 4
        assert hasattr(btx.fs.unit.outlet_1, "flow_mol")
        assert hasattr(btx.fs.unit.outlet_1, "mole_frac_comp")
        assert hasattr(btx.fs.unit.outlet_1, "temperature")
        assert hasattr(btx.fs.unit.outlet_1, "pressure")

        assert hasattr(btx.fs.unit, "outlet_2")
        assert len(btx.fs.unit.outlet_2.vars) == 4
        assert hasattr(btx.fs.unit.outlet_2, "flow_mol")
        assert hasattr(btx.fs.unit.outlet_2, "mole_frac_comp")
        assert hasattr(btx.fs.unit.outlet_2, "temperature")
        assert hasattr(btx.fs.unit.outlet_2, "pressure")

        assert isinstance(btx.fs.unit.overall_heat_transfer_coefficient, Var)
        assert isinstance(btx.fs.unit.area, Var)
        assert not hasattr(btx.fs.unit, "crossflow_factor")
        assert isinstance(btx.fs.unit.heat_duty, Var)
        assert isinstance(btx.fs.unit.delta_temperature_in, Var)
        assert isinstance(btx.fs.unit.delta_temperature_out, Var)
        assert isinstance(btx.fs.unit.unit_heat_balance, Constraint)
        assert isinstance(btx.fs.unit.delta_temperature, (Var, Expression))
        assert isinstance(btx.fs.unit.heat_transfer_equation, Constraint)

        assert number_variables(btx) == 50
        assert number_total_constraints(btx) == 38
        assert number_unused_variables(btx) == 0

    @pytest.mark.unit
    def test_dof(self, btx):
        btx.fs.unit.inlet_1.flow_mol[0].fix(5)  # mol/s
        btx.fs.unit.inlet_1.temperature[0].fix(365)  # K
        btx.fs.unit.inlet_1.pressure[0].fix(101325)  # Pa
        btx.fs.unit.inlet_1.mole_frac_comp[0, "benzene"].fix(0.5)
        btx.fs.unit.inlet_1.mole_frac_comp[0, "toluene"].fix(0.5)

        btx.fs.unit.inlet_2.flow_mol[0].fix(1)  # mol/s
        btx.fs.unit.inlet_2.temperature[0].fix(300)  # K
        btx.fs.unit.inlet_2.pressure[0].fix(101325)  # Pa
        btx.fs.unit.inlet_2.mole_frac_comp[0, "benzene"].fix(0.5)
        btx.fs.unit.inlet_2.mole_frac_comp[0, "toluene"].fix(0.5)

        btx.fs.unit.area.fix(1)
        btx.fs.unit.overall_heat_transfer_coefficient.fix(100)

        assert degrees_of_freedom(btx) == 0

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_initialize(self, btx):
        initialization_tester(btx)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solve(self, btx):
        results = solver.solve(btx)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solution(self, btx):
        assert (pytest.approx(5, abs=1e-3) ==
                value(btx.fs.unit.outlet_1.flow_mol[0]))
        assert (pytest.approx(359.5, abs=1e-1) ==
                value(btx.fs.unit.outlet_1.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx.fs.unit.outlet_1.pressure[0]))

        assert (pytest.approx(1, abs=1e-3) ==
                value(btx.fs.unit.outlet_2.flow_mol[0]))
        assert (pytest.approx(329.9, abs=1e-1) ==
                value(btx.fs.unit.outlet_2.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx.fs.unit.outlet_2.pressure[0]))

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_conservation(self, btx):
        assert abs(value(btx.fs.unit.inlet_1.flow_mol[0] -
                         btx.fs.unit.outlet_1.flow_mol[0])) <= 1e-6
        assert abs(value(btx.fs.unit.inlet_2.flow_mol[0] -
                         btx.fs.unit.outlet_2.flow_mol[0])) <= 1e-6

        shell = value(
                btx.fs.unit.outlet_1.flow_mol[0] *
                (btx.fs.unit.shell.properties_in[0].enth_mol_phase['Liq'] -
                 btx.fs.unit.shell.properties_out[0].enth_mol_phase['Liq']))
        tube = value(
                btx.fs.unit.outlet_2.flow_mol[0] *
                (btx.fs.unit.tube.properties_in[0].enth_mol_phase['Liq'] -
                 btx.fs.unit.tube.properties_out[0].enth_mol_phase['Liq']))
        assert abs(shell + tube) <= 1e-6

    @pytest.mark.ui
    @pytest.mark.unit
    def test_report(self, btx):
        btx.fs.unit.report()

# -----------------------------------------------------------------------------
class TestBTX_cocurrent_alt_name(object):
    @pytest.fixture(scope="class")
    def btx(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = BTXParameterBlock(default={"valid_phase": 'Liq'})

        m.fs.unit = HeatExchanger(default={
                "hot_side_name":"hot",
                "cold_side_name":"cold",
                "hot": {"property_package": m.fs.properties},
                "cold": {"property_package": m.fs.properties},
                "flow_pattern": HeatExchangerFlowPattern.cocurrent})

        return m

    @pytest.mark.build
    @pytest.mark.unit
    def test_build(self, btx):
        assert hasattr(btx.fs.unit, "hot_inlet")
        assert len(btx.fs.unit.hot_inlet.vars) == 4
        assert hasattr(btx.fs.unit.hot_inlet, "flow_mol")
        assert hasattr(btx.fs.unit.hot_inlet, "mole_frac_comp")
        assert hasattr(btx.fs.unit.hot_inlet, "temperature")
        assert hasattr(btx.fs.unit.hot_inlet, "pressure")

        assert hasattr(btx.fs.unit, "cold_inlet")
        assert len(btx.fs.unit.cold_inlet.vars) == 4
        assert hasattr(btx.fs.unit.cold_inlet, "flow_mol")
        assert hasattr(btx.fs.unit.cold_inlet, "mole_frac_comp")
        assert hasattr(btx.fs.unit.cold_inlet, "temperature")
        assert hasattr(btx.fs.unit.cold_inlet, "pressure")

        assert hasattr(btx.fs.unit, "hot_outlet")
        assert len(btx.fs.unit.hot_outlet.vars) == 4
        assert hasattr(btx.fs.unit.hot_outlet, "flow_mol")
        assert hasattr(btx.fs.unit.hot_outlet, "mole_frac_comp")
        assert hasattr(btx.fs.unit.hot_outlet, "temperature")
        assert hasattr(btx.fs.unit.hot_outlet, "pressure")

        assert hasattr(btx.fs.unit, "cold_outlet")
        assert len(btx.fs.unit.cold_outlet.vars) == 4
        assert hasattr(btx.fs.unit.cold_outlet, "flow_mol")
        assert hasattr(btx.fs.unit.cold_outlet, "mole_frac_comp")
        assert hasattr(btx.fs.unit.cold_outlet, "temperature")
        assert hasattr(btx.fs.unit.cold_outlet, "pressure")

        assert isinstance(btx.fs.unit.overall_heat_transfer_coefficient, Var)
        assert isinstance(btx.fs.unit.area, Var)
        assert not hasattr(btx.fs.unit, "crossflow_factor")
        assert isinstance(btx.fs.unit.heat_duty, Var)
        assert isinstance(btx.fs.unit.delta_temperature_in, Var)
        assert isinstance(btx.fs.unit.delta_temperature_out, Var)
        assert isinstance(btx.fs.unit.unit_heat_balance, Constraint)
        assert isinstance(btx.fs.unit.delta_temperature, (Var, Expression))
        assert isinstance(btx.fs.unit.heat_transfer_equation, Constraint)

        assert number_variables(btx) == 50
        assert number_total_constraints(btx) == 38
        assert number_unused_variables(btx) == 0

    @pytest.mark.unit
    def test_dof(self, btx):
        btx.fs.unit.hot_inlet.flow_mol[0].fix(5)  # mol/s
        btx.fs.unit.hot_inlet.temperature[0].fix(365)  # K
        btx.fs.unit.hot_inlet.pressure[0].fix(101325)  # Pa
        btx.fs.unit.hot_inlet.mole_frac_comp[0, "benzene"].fix(0.5)
        btx.fs.unit.hot_inlet.mole_frac_comp[0, "toluene"].fix(0.5)

        btx.fs.unit.cold_inlet.flow_mol[0].fix(1)  # mol/s
        btx.fs.unit.cold_inlet.temperature[0].fix(300)  # K
        btx.fs.unit.cold_inlet.pressure[0].fix(101325)  # Pa
        btx.fs.unit.cold_inlet.mole_frac_comp[0, "benzene"].fix(0.5)
        btx.fs.unit.cold_inlet.mole_frac_comp[0, "toluene"].fix(0.5)

        btx.fs.unit.area.fix(1)
        btx.fs.unit.overall_heat_transfer_coefficient.fix(100)

        assert degrees_of_freedom(btx) == 0

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_initialize(self, btx):
        initialization_tester(btx)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solve(self, btx):
        results = solver.solve(btx)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solution(self, btx):
        assert (pytest.approx(5, abs=1e-3) ==
                value(btx.fs.unit.hot_outlet.flow_mol[0]))
        assert (pytest.approx(359.5, abs=1e-1) ==
                value(btx.fs.unit.hot_outlet.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx.fs.unit.hot_outlet.pressure[0]))

        assert (pytest.approx(1, abs=1e-3) ==
                value(btx.fs.unit.cold_outlet.flow_mol[0]))
        assert (pytest.approx(329.9, abs=1e-1) ==
                value(btx.fs.unit.cold_outlet.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx.fs.unit.cold_outlet.pressure[0]))

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_conservation(self, btx):
        assert abs(value(btx.fs.unit.hot_inlet.flow_mol[0] -
                         btx.fs.unit.hot_outlet.flow_mol[0])) <= 1e-6
        assert abs(value(btx.fs.unit.cold_inlet.flow_mol[0] -
                         btx.fs.unit.cold_outlet.flow_mol[0])) <= 1e-6

        shell = value(
                btx.fs.unit.hot_outlet.flow_mol[0] *
                (btx.fs.unit.hot.properties_in[0].enth_mol_phase['Liq'] -
                 btx.fs.unit.hot.properties_out[0].enth_mol_phase['Liq']))
        tube = value(
                btx.fs.unit.cold_outlet.flow_mol[0] *
                (btx.fs.unit.cold.properties_in[0].enth_mol_phase['Liq'] -
                 btx.fs.unit.cold.properties_out[0].enth_mol_phase['Liq']))
        assert abs(shell + tube) <= 1e-6

    @pytest.mark.ui
    @pytest.mark.unit
    def test_report(self, btx):
        btx.fs.unit.report()


# -----------------------------------------------------------------------------
@pytest.mark.iapws
@pytest.mark.skipif(not iapws95.iapws95_available(),
                    reason="IAPWS not available")
class TestIAPWS_countercurrent(object):
    @pytest.fixture(scope="class")
    def iapws(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = iapws95.Iapws95ParameterBlock()

        m.fs.unit = HeatExchanger(default={
                "shell": {"property_package": m.fs.properties},
                "tube": {"property_package": m.fs.properties},
                "flow_pattern": HeatExchangerFlowPattern.countercurrent})

        return m

    @pytest.mark.build
    @pytest.mark.unit
    def test_build(self, iapws):
        assert len(iapws.fs.unit.inlet_1.vars) == 3
        assert hasattr(iapws.fs.unit.inlet_1, "flow_mol")
        assert hasattr(iapws.fs.unit.inlet_1, "enth_mol")
        assert hasattr(iapws.fs.unit.inlet_1, "pressure")

        assert hasattr(iapws.fs.unit, "outlet_1")
        assert len(iapws.fs.unit.outlet_1.vars) == 3
        assert hasattr(iapws.fs.unit.outlet_1, "flow_mol")
        assert hasattr(iapws.fs.unit.outlet_1, "enth_mol")
        assert hasattr(iapws.fs.unit.outlet_1, "pressure")

        assert len(iapws.fs.unit.inlet_2.vars) == 3
        assert hasattr(iapws.fs.unit.inlet_2, "flow_mol")
        assert hasattr(iapws.fs.unit.inlet_2, "enth_mol")
        assert hasattr(iapws.fs.unit.inlet_2, "pressure")

        assert hasattr(iapws.fs.unit, "outlet_2")
        assert len(iapws.fs.unit.outlet_2.vars) == 3
        assert hasattr(iapws.fs.unit.outlet_2, "flow_mol")
        assert hasattr(iapws.fs.unit.outlet_2, "enth_mol")
        assert hasattr(iapws.fs.unit.outlet_2, "pressure")

        assert isinstance(iapws.fs.unit.overall_heat_transfer_coefficient, Var)
        assert isinstance(iapws.fs.unit.area, Var)
        assert not hasattr(iapws.fs.unit, "crossflow_factor")
        assert isinstance(iapws.fs.unit.heat_duty, Var)
        assert isinstance(iapws.fs.unit.delta_temperature_in, Var)
        assert isinstance(iapws.fs.unit.delta_temperature_out, Var)
        assert isinstance(iapws.fs.unit.unit_heat_balance, Constraint)
        assert isinstance(iapws.fs.unit.delta_temperature, (Expression, Var))
        assert isinstance(iapws.fs.unit.heat_transfer_equation, Constraint)

        assert number_variables(iapws) == 18
        assert number_total_constraints(iapws) == 10
        assert number_unused_variables(iapws) == 0

    @pytest.mark.unit
    def test_dof(self, iapws):
        iapws.fs.unit.inlet_1.flow_mol[0].fix(100)
        iapws.fs.unit.inlet_1.enth_mol[0].fix(4000)
        iapws.fs.unit.inlet_1.pressure[0].fix(101325)

        iapws.fs.unit.inlet_2.flow_mol[0].fix(100)
        iapws.fs.unit.inlet_2.enth_mol[0].fix(3500)
        iapws.fs.unit.inlet_2.pressure[0].fix(101325)

        iapws.fs.unit.area.fix(1000)
        iapws.fs.unit.overall_heat_transfer_coefficient.fix(100)

        assert degrees_of_freedom(iapws) == 0

    @pytest.mark.unit
    def test_dof_alt_name1(self, iapws):
        iapws.fs.unit.shell_inlet.flow_mol[0].fix(100)
        iapws.fs.unit.shell_inlet.enth_mol[0].fix(4000)
        iapws.fs.unit.shell_inlet.pressure[0].fix(101325)

        iapws.fs.unit.tube_inlet.flow_mol[0].fix(100)
        iapws.fs.unit.tube_inlet.enth_mol[0].fix(3500)
        iapws.fs.unit.tube_inlet.pressure[0].fix(101325)

        iapws.fs.unit.area.fix(1000)
        iapws.fs.unit.overall_heat_transfer_coefficient.fix(100)

        assert degrees_of_freedom(iapws) == 0

    @pytest.mark.initialization
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_initialize(self, iapws):
        initialization_tester(iapws)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solve(self, iapws):
        results = solver.solve(iapws)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solution(self, iapws):
        assert pytest.approx(100, abs=1e-5) == \
            value(iapws.fs.unit.outlet_1.flow_mol[0])
        assert pytest.approx(100, abs=1e-5) == \
            value(iapws.fs.unit.outlet_2.flow_mol[0])

        assert pytest.approx(3535, abs=1e0) == \
            value(iapws.fs.unit.outlet_1.enth_mol[0])
        assert pytest.approx(3964.5, abs=1e0) == \
            value(iapws.fs.unit.outlet_2.enth_mol[0])

        assert pytest.approx(101325, abs=1e2) == \
            value(iapws.fs.unit.outlet_1.pressure[0])
        assert pytest.approx(101325, abs=1e2) == \
            value(iapws.fs.unit.outlet_2.pressure[0])

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_conservation(self, iapws):
        assert abs(value(iapws.fs.unit.inlet_1.flow_mol[0] -
                         iapws.fs.unit.outlet_1.flow_mol[0])) <= 1e-6
        assert abs(value(iapws.fs.unit.inlet_2.flow_mol[0] -
                         iapws.fs.unit.outlet_2.flow_mol[0])) <= 1e-6

        shell_side = value(
                iapws.fs.unit.outlet_1.flow_mol[0] *
                (iapws.fs.unit.inlet_1.enth_mol[0] -
                 iapws.fs.unit.outlet_1.enth_mol[0]))
        tube_side = value(
                iapws.fs.unit.outlet_2.flow_mol[0] *
                (iapws.fs.unit.inlet_2.enth_mol[0] -
                 iapws.fs.unit.outlet_2.enth_mol[0]))
        assert abs(shell_side + tube_side) <= 1e-6

    @pytest.mark.ui
    @pytest.mark.unit
    def test_report(self, iapws):
        iapws.fs.unit.report()


# -----------------------------------------------------------------------------
#@pytest.mark.skip(reason="Solutions vary with differnt versions of solver.")
class TestSaponification_crossflow(object):
    @pytest.fixture(scope="class")
    def sapon(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = SaponificationParameterBlock()

        m.fs.unit = HeatExchanger(default={
                "shell": {"property_package": m.fs.properties},
                "tube": {"property_package": m.fs.properties},
                "flow_pattern": HeatExchangerFlowPattern.crossflow})

        return m

    @pytest.mark.build
    @pytest.mark.unit
    def test_build(self, sapon):
        assert len(sapon.fs.unit.inlet_1.vars) == 4
        assert hasattr(sapon.fs.unit.inlet_1, "flow_vol")
        assert hasattr(sapon.fs.unit.inlet_1, "conc_mol_comp")
        assert hasattr(sapon.fs.unit.inlet_1, "temperature")
        assert hasattr(sapon.fs.unit.inlet_1, "pressure")

        assert len(sapon.fs.unit.outlet_1.vars) == 4
        assert hasattr(sapon.fs.unit.outlet_1, "flow_vol")
        assert hasattr(sapon.fs.unit.outlet_1, "conc_mol_comp")
        assert hasattr(sapon.fs.unit.outlet_1, "temperature")
        assert hasattr(sapon.fs.unit.outlet_1, "pressure")

        assert len(sapon.fs.unit.inlet_2.vars) == 4
        assert hasattr(sapon.fs.unit.inlet_2, "flow_vol")
        assert hasattr(sapon.fs.unit.inlet_2, "conc_mol_comp")
        assert hasattr(sapon.fs.unit.inlet_2, "temperature")
        assert hasattr(sapon.fs.unit.inlet_2, "pressure")

        assert len(sapon.fs.unit.outlet_2.vars) == 4
        assert hasattr(sapon.fs.unit.outlet_2, "flow_vol")
        assert hasattr(sapon.fs.unit.outlet_2, "conc_mol_comp")
        assert hasattr(sapon.fs.unit.outlet_2, "temperature")
        assert hasattr(sapon.fs.unit.outlet_2, "pressure")

        assert isinstance(sapon.fs.unit.overall_heat_transfer_coefficient, Var)
        assert isinstance(sapon.fs.unit.area, Var)
        assert isinstance(sapon.fs.unit.crossflow_factor, Var)
        assert isinstance(sapon.fs.unit.heat_duty, Var)
        assert isinstance(sapon.fs.unit.delta_temperature_in, Var)
        assert isinstance(sapon.fs.unit.delta_temperature_out, Var)
        assert isinstance(sapon.fs.unit.unit_heat_balance, Constraint)
        assert isinstance(sapon.fs.unit.delta_temperature, (Expression,Var))
        assert isinstance(sapon.fs.unit.heat_transfer_equation, Constraint)

        assert number_variables(sapon) == 39
        assert number_total_constraints(sapon) == 20
        assert number_unused_variables(sapon) == 0

    @pytest.mark.unit
    def test_dof(self, sapon):
        sapon.fs.unit.inlet_1.flow_vol[0].fix(1e-3)
        sapon.fs.unit.inlet_1.temperature[0].fix(320)
        sapon.fs.unit.inlet_1.pressure[0].fix(101325)
        sapon.fs.unit.inlet_1.conc_mol_comp[0, "H2O"].fix(55388.0)
        sapon.fs.unit.inlet_1.conc_mol_comp[0, "NaOH"].fix(100.0)
        sapon.fs.unit.inlet_1.conc_mol_comp[0, "EthylAcetate"].fix(100.0)
        sapon.fs.unit.inlet_1.conc_mol_comp[0, "SodiumAcetate"].fix(0.0)
        sapon.fs.unit.inlet_1.conc_mol_comp[0, "Ethanol"].fix(0.0)

        sapon.fs.unit.inlet_2.flow_vol[0].fix(1e-3)
        sapon.fs.unit.inlet_2.temperature[0].fix(300)
        sapon.fs.unit.inlet_2.pressure[0].fix(101325)
        sapon.fs.unit.inlet_2.conc_mol_comp[0, "H2O"].fix(55388.0)
        sapon.fs.unit.inlet_2.conc_mol_comp[0, "NaOH"].fix(100.0)
        sapon.fs.unit.inlet_2.conc_mol_comp[0, "EthylAcetate"].fix(100.0)
        sapon.fs.unit.inlet_2.conc_mol_comp[0, "SodiumAcetate"].fix(0.0)
        sapon.fs.unit.inlet_2.conc_mol_comp[0, "Ethanol"].fix(0.0)

        sapon.fs.unit.area.fix(1000)
        sapon.fs.unit.overall_heat_transfer_coefficient.fix(100)
        sapon.fs.unit.crossflow_factor.fix(0.6)

        assert degrees_of_freedom(sapon) == 0

    @pytest.mark.initialization
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_initialize(self, sapon):
        initialization_tester(sapon)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solve(self, sapon):
        results = solver.solve(sapon)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_solution(self, sapon):
        assert pytest.approx(1e-3, abs=1e-6) == \
            value(sapon.fs.unit.outlet_1.flow_vol[0])
        assert pytest.approx(1e-3, abs=1e-6) == \
            value(sapon.fs.unit.outlet_2.flow_vol[0])

        assert pytest.approx(55388.0, rel=1e-3) == value(
                sapon.fs.unit.outlet_1.conc_mol_comp[0, "H2O"])
        assert pytest.approx(100.0, rel=1e-3) == value(
                sapon.fs.unit.outlet_1.conc_mol_comp[0, "NaOH"])
        assert pytest.approx(100.0, rel=1e-3) == value(
                sapon.fs.unit.outlet_1.conc_mol_comp[0, "EthylAcetate"])
        assert pytest.approx(0.0, abs=1e-3) == value(
                sapon.fs.unit.outlet_1.conc_mol_comp[0, "SodiumAcetate"])
        assert pytest.approx(0.0, abs=1e-3) == value(
                sapon.fs.unit.outlet_1.conc_mol_comp[0, "Ethanol"])

        assert pytest.approx(55388.0, rel=1e-3) == value(
                sapon.fs.unit.outlet_2.conc_mol_comp[0, "H2O"])
        assert pytest.approx(100.0, rel=1e-3) == value(
                sapon.fs.unit.outlet_2.conc_mol_comp[0, "NaOH"])
        assert pytest.approx(100.0, rel=1e-3) == value(
                sapon.fs.unit.outlet_2.conc_mol_comp[0, "EthylAcetate"])
        assert pytest.approx(0.0, abs=1e-3) == value(
                sapon.fs.unit.outlet_2.conc_mol_comp[0, "SodiumAcetate"])
        assert pytest.approx(0.0, abs=1e-3) == value(
                sapon.fs.unit.outlet_2.conc_mol_comp[0, "Ethanol"])

        assert pytest.approx(301.3, abs=1e-1) == \
            value(sapon.fs.unit.outlet_1.temperature[0])
        assert pytest.approx(318.7, abs=1e-1) == \
            value(sapon.fs.unit.outlet_2.temperature[0])

        assert pytest.approx(101325, abs=1e2) == \
            value(sapon.fs.unit.outlet_1.pressure[0])
        assert pytest.approx(101325, abs=1e2) == \
            value(sapon.fs.unit.outlet_2.pressure[0])

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.unit
    def test_conservation(self, sapon):
        shell_side = value(
                sapon.fs.unit.outlet_1.flow_vol[0] *
                sapon.fs.properties.dens_mol*sapon.fs.properties.cp_mol *
                (sapon.fs.unit.inlet_1.temperature[0] -
                 sapon.fs.unit.outlet_1.temperature[0]))
        tube_side = value(
                sapon.fs.unit.outlet_2.flow_vol[0] *
                sapon.fs.properties.dens_mol*sapon.fs.properties.cp_mol *
                (sapon.fs.unit.inlet_2.temperature[0] -
                 sapon.fs.unit.outlet_2.temperature[0]))
        assert abs(shell_side + tube_side) <= 1e0

    @pytest.mark.ui
    @pytest.mark.unit
    def test_report(self, sapon):
        sapon.fs.unit.report()
