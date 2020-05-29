##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2019, by the
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
Tests for total condenser unit model.Tests 2 sets of state vars using the ideal
property package (FTPz and FcTP).

Author: Jaffer Ghouse
"""
import pytest
from pyomo.environ import (ConcreteModel, TerminationCondition,
                           SolverStatus, value)

from idaes.core import (FlowsheetBlock, MaterialBalanceType, EnergyBalanceType,
                        MomentumBalanceType)
from idaes.generic_models.unit_models.distillation import Condenser
from idaes.generic_models.unit_models.distillation.condenser import CondenserType, \
    TemperatureSpec
from idaes.generic_models.properties.activity_coeff_models.BTX_activity_coeff_VLE \
    import BTXParameterBlock
from idaes.core.util.model_statistics import degrees_of_freedom, \
    number_variables, number_total_constraints, number_unused_variables, \
    fixed_variables_set, activated_constraints_set
from idaes.core.util.testing import get_default_solver, \
    PhysicalParameterTestBlock, initialization_tester


# -----------------------------------------------------------------------------
# Get default solver for testing
solver = get_default_solver()


def test_config():

    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    m.fs.properties = PhysicalParameterTestBlock()

    m.fs.unit = Condenser(
        default={"property_package": m.fs.properties,
                 "condenser_type": CondenserType.totalCondenser,
                 "temperature_spec": TemperatureSpec.customTemperature})

    assert len(m.fs.unit.config) == 10
    assert m.fs.unit.config.condenser_type == CondenserType.totalCondenser
    assert m.fs.unit.config.material_balance_type == \
        MaterialBalanceType.useDefault
    assert m.fs.unit.config.energy_balance_type == \
        EnergyBalanceType.useDefault
    assert m.fs.unit.config.momentum_balance_type == \
        MomentumBalanceType.pressureTotal
    assert not m.fs.unit.config.has_pressure_change
    assert hasattr(m.fs.unit, "heat_duty")


class TestBTXIdeal(object):
    @pytest.fixture(scope="class")
    def btx_ftpz(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                                     ('Liq', 'Vap'),
                                                     "activity_coeff_model":
                                                     "Ideal"})

        m.fs.unit = Condenser(
            default={"property_package": m.fs.properties,
                     "condenser_type": CondenserType.totalCondenser,
                     "temperature_spec": TemperatureSpec.atBubblePoint,
                     "has_pressure_change": True})

        return m

    @pytest.fixture(scope="class")
    def btx_fctp(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                                     ('Liq', 'Vap'),
                                                     "activity_coeff_model":
                                                     "Ideal",
                                                     "state_vars": "FcTP"})

        m.fs.unit = Condenser(
            default={"property_package": m.fs.properties,
                     "condenser_type": CondenserType.totalCondenser,
                     "temperature_spec": TemperatureSpec.atBubblePoint,
                     "has_pressure_change": True})

        return m

    @pytest.mark.build
    def test_build(self, btx_ftpz, btx_fctp):
        assert hasattr(btx_ftpz.fs.unit, "reflux_ratio")
        assert hasattr(btx_ftpz.fs.unit, "eq_total_cond_spec")

        assert hasattr(btx_ftpz.fs.unit, "inlet")

        assert hasattr(btx_ftpz.fs.unit.inlet, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.inlet, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.inlet, "temperature")
        assert hasattr(btx_ftpz.fs.unit.inlet, "pressure")

        assert hasattr(btx_ftpz.fs.unit, "reflux")

        assert hasattr(btx_ftpz.fs.unit.reflux, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.reflux, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.reflux, "temperature")
        assert hasattr(btx_ftpz.fs.unit.reflux, "pressure")

        assert hasattr(btx_ftpz.fs.unit, "distillate")
        assert hasattr(btx_ftpz.fs.unit.distillate, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.distillate, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.distillate, "temperature")
        assert hasattr(btx_ftpz.fs.unit.distillate, "pressure")

        assert number_variables(btx_ftpz.fs.unit) == 49
        assert number_total_constraints(btx_ftpz.fs.unit) == 42
        assert number_unused_variables(btx_ftpz) == 1

        assert hasattr(btx_fctp.fs.unit, "reflux_ratio")
        assert hasattr(btx_fctp.fs.unit, "eq_total_cond_spec")

        assert hasattr(btx_fctp.fs.unit, "inlet")

        assert hasattr(btx_fctp.fs.unit.inlet, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.inlet, "temperature")
        assert hasattr(btx_fctp.fs.unit.inlet, "pressure")

        assert hasattr(btx_fctp.fs.unit, "reflux")

        assert hasattr(btx_fctp.fs.unit.reflux, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.reflux, "temperature")
        assert hasattr(btx_fctp.fs.unit.reflux, "pressure")

        assert hasattr(btx_fctp.fs.unit, "distillate")
        assert hasattr(btx_fctp.fs.unit.distillate, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.distillate, "temperature")
        assert hasattr(btx_fctp.fs.unit.distillate, "pressure")

        assert number_variables(btx_fctp.fs.unit) == 51
        assert number_total_constraints(btx_fctp.fs.unit) == 45
        assert number_unused_variables(btx_fctp) == 1

    def test_dof(self, btx_ftpz, btx_fctp):

        # Fix the total condenser variables (FTPz)
        btx_ftpz.fs.unit.reflux_ratio.fix(1)
        btx_ftpz.fs.unit.deltaP.fix(0)

        # Fix the inputs (typically this will be the vapor from the top tray)
        btx_ftpz.fs.unit.inlet.flow_mol.fix(1)
        btx_ftpz.fs.unit.inlet.temperature.fix(375)
        btx_ftpz.fs.unit.inlet.pressure.fix(101325)
        btx_ftpz.fs.unit.inlet.mole_frac_comp[0, "benzene"].fix(0.5)
        btx_ftpz.fs.unit.inlet.mole_frac_comp[0, "toluene"].fix(0.5)

        assert degrees_of_freedom(btx_ftpz) == 0

        # Fix the total condenser variables (FcTP)
        btx_fctp.fs.unit.reflux_ratio.fix(1)
        btx_fctp.fs.unit.deltaP.fix(0)

        # Fix the inputs (typically this will be the outlet vapor from the top tray)
        btx_fctp.fs.unit.inlet.flow_mol_comp[0, "benzene"].fix(0.5)
        btx_fctp.fs.unit.inlet.flow_mol_comp[0, "toluene"].fix(0.5)
        btx_fctp.fs.unit.inlet.temperature.fix(375)
        btx_fctp.fs.unit.inlet.pressure.fix(101325)

        assert degrees_of_freedom(btx_fctp) == 0

    @pytest.mark.initialization
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_initialize(self, btx_ftpz, btx_fctp):
        initialization_tester(btx_ftpz)
        initialization_tester(btx_fctp)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solve(self, btx_ftpz, btx_fctp):
        results = solver.solve(btx_ftpz)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

        results = solver.solve(btx_fctp)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solution(self, btx_ftpz, btx_fctp):
        # Reflux port
        assert (pytest.approx(0.4999, abs=1e-3) ==
                value(btx_ftpz.fs.unit.reflux.flow_mol[0]))
        assert (pytest.approx(0.5, abs=1e-3) ==
                value(btx_ftpz.fs.unit.reflux.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.5, abs=1e-3) ==
                value(btx_ftpz.fs.unit.reflux.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(365.347, abs=1e-3) ==
                value(btx_ftpz.fs.unit.reflux.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.reflux.pressure[0]))

        # Distillate port
        assert (pytest.approx(0.4999, abs=1e-3) ==
                value(btx_ftpz.fs.unit.distillate.flow_mol[0]))
        assert (pytest.approx(0.5, abs=1e-3) ==
                value(btx_ftpz.fs.unit.distillate.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.5, abs=1e-3) ==
                value(btx_ftpz.fs.unit.distillate.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(365.347, abs=1e-3) ==
                value(btx_ftpz.fs.unit.distillate.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.distillate.pressure[0]))

        # Unit level
        assert (pytest.approx(-33711.313, abs=1e-3) ==
                value(btx_ftpz.fs.unit.heat_duty[0]))

        # Reflux port
        assert (pytest.approx(0.25, abs=1e-3) ==
                value(btx_fctp.fs.unit.reflux.flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(0.25, abs=1e-3) ==
                value(btx_fctp.fs.unit.reflux.flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(365.347, abs=1e-3) ==
                value(btx_fctp.fs.unit.reflux.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.reflux.pressure[0]))

        # Distillate port
        assert (pytest.approx(0.25, abs=1e-3) ==
                value(btx_fctp.fs.unit.distillate.flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(0.25, abs=1e-3) ==
                value(btx_fctp.fs.unit.distillate.flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(365.347, abs=1e-3) ==
                value(btx_fctp.fs.unit.distillate.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.distillate.pressure[0]))

        # Unit level
        assert (pytest.approx(-33711.295, abs=1e-3) ==
                value(btx_fctp.fs.unit.heat_duty[0]))

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_conservation(self, btx_ftpz, btx_fctp):
        assert abs(value(btx_ftpz.fs.unit.inlet.flow_mol[0] -
                         (btx_ftpz.fs.unit.reflux.flow_mol[0] +
                          btx_ftpz.fs.unit.distillate.flow_mol[0]))) <= 1e-6

        assert abs(value(btx_fctp.fs.unit.inlet.flow_mol_comp[0, "benzene"] +
                         btx_fctp.fs.unit.inlet.flow_mol_comp[0, "toluene"] -
                         (btx_fctp.fs.unit.reflux.flow_mol_comp[0, "benzene"] +
                          btx_fctp.fs.unit.reflux.flow_mol_comp[0, "toluene"] +
                          btx_fctp.fs.unit.distillate.
                          flow_mol_comp[0, "benzene"] +
                          btx_fctp.fs.unit.distillate.
                          flow_mol_comp[0, "toluene"]))) <= 1e-6

    @pytest.mark.ui
    def test_report(self, btx_ftpz, btx_fctp):
        btx_ftpz.fs.unit.report()
        btx_fctp.fs.unit.report()