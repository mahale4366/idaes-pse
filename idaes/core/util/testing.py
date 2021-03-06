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
This module contains utility functions for use in testing IDAES models.
"""

__author__ = "Andrew Lee"


from pyomo.environ import Constraint, Set, SolverFactory, units, Var
from pyomo.common.config import ConfigBlock

from idaes.core import (declare_process_block_class,
                        PhysicalParameterBlock,
                        StateBlock,
                        StateBlockData,
                        ReactionParameterBlock,
                        ReactionBlockBase,
                        ReactionBlockDataBase,
                        MaterialFlowBasis,
                        MaterialBalanceType,
                        EnergyBalanceType,
                        Component,
                        Phase)

from idaes.core.util.model_statistics import (degrees_of_freedom,
                                              fixed_variables_set,
                                              activated_constraints_set)


def get_default_solver():
    """
    Tries to set-up the default solver for testing, and returns None if not
    available
    """
    if SolverFactory('ipopt').available(exception_flag=False):
        solver = SolverFactory('ipopt')
        solver.options = {'tol': 1e-6,
                          'linear_solver': 'ma27'}
    else:
        solver = None

    return solver


def initialization_tester(m, dof=0, **init_kwargs):
    """
    A method to test initialization methods on IDAES models. This method is
    designed to be used as part of the tests for most models.

    This method checks that the initialization methods runs as expceted
    and that the state of the model (active/deactive and fixed/unfixed)
    remains the same.

    This method also add some dummy constraitns to the model and deactivates
    them to make sure that the initialization does not affect their status.

    Args:
        m: a Concrete mdoel which contains a flowsheet and a model named unit
            (i.e. m.fs.unit) which will be initialized
        dof: expected degrees of freedom during initialization, default=0
        init_kwargs: model specific arguments to pass to initialize method
                     (e.g. initial guesses for states)

    Returns:
        None

    Raises:
        AssertionErrors is an issue is found
    """
    # Add some extra constraints and deactivate them to make sure
    # they remain deactivated
    # Test both indexed and unindexed constraints
    m.fs.unit.__dummy_var = Var()
    m.fs.unit.__dummy_equality = Constraint(expr=m.fs.unit.__dummy_var == 5)
    m.fs.unit.__dummy_inequality = Constraint(expr=m.fs.unit.__dummy_var <= 10)

    def deq_idx(b, i):
        return m.fs.unit.__dummy_var == 5
    m.fs.unit.__dummy_equality_idx = Constraint([1], rule=deq_idx)

    def dieq_idx(b, i):
        return m.fs.unit.__dummy_var <= 10
    m.fs.unit.__dummy_inequality_idx = Constraint([1], rule=dieq_idx)

    m.fs.unit.__dummy_equality.deactivate()
    m.fs.unit.__dummy_inequality.deactivate()
    m.fs.unit.__dummy_equality_idx[1].deactivate()
    m.fs.unit.__dummy_inequality_idx[1].deactivate()

    orig_fixed_vars = fixed_variables_set(m)
    orig_act_consts = activated_constraints_set(m)

    m.fs.unit.initialize(**init_kwargs)

    print(degrees_of_freedom(m))
    assert degrees_of_freedom(m) == dof

    fin_fixed_vars = fixed_variables_set(m)
    fin_act_consts = activated_constraints_set(m)

    assert len(fin_act_consts) == len(orig_act_consts)
    assert len(fin_fixed_vars) == len(orig_fixed_vars)

    for c in fin_act_consts:
        assert c in orig_act_consts
    for v in fin_fixed_vars:
        assert v in orig_fixed_vars

    # Check dummy constraints and clean up
    assert not m.fs.unit.__dummy_equality.active
    assert not m.fs.unit.__dummy_inequality.active
    assert not m.fs.unit.__dummy_equality_idx[1].active
    assert not m.fs.unit.__dummy_inequality_idx[1].active

    m.fs.unit.del_component(m.fs.unit.__dummy_inequality)
    m.fs.unit.del_component(m.fs.unit.__dummy_equality)
    m.fs.unit.del_component(m.fs.unit.__dummy_inequality_idx)
    m.fs.unit.del_component(m.fs.unit.__dummy_equality_idx)
    m.fs.unit.del_component(m.fs.unit.__dummy_var)

# -----------------------------------------------------------------------------
# Define some generic PhysicalBlock and ReactionBlock classes for testing
@declare_process_block_class("PhysicalParameterTestBlock")
class _PhysicalParameterBlock(PhysicalParameterBlock):
    def build(self):
        super(_PhysicalParameterBlock, self).build()

        self.p1 = Phase()
        self.p2 = Phase()

        self.c1 = Component()
        self.c2 = Component()

        self.phase_equilibrium_idx = Set(initialize=["e1", "e2"])
        self.element_list = Set(initialize=["H", "He", "Li"])
        self.element_comp = {"c1": {"H": 1, "He": 2, "Li": 3},
                             "c2": {"H": 4, "He": 5, "Li": 6}}

        self.phase_equilibrium_list = \
            {"e1": ["c1", ("p1", "p2")],
             "e2": ["c2", ("p1", "p2")]}

        # Attribute to switch flow basis for testing
        self.basis_switch = 1
        self.default_balance_switch = 1

        self._state_block_class = TestStateBlock

    @classmethod
    def define_metadata(cls, obj):
        obj.add_default_units({'time': units.s,
                               'length': units.m,
                               'mass': units.kg,
                               'amount': units.mol,
                               'temperature': units.K})


class SBlockBase(StateBlock):
    def initialize(blk, outlvl=0, optarg=None, solver=None,
                   hold_state=False, **state_args):
        for k in blk.keys():
            blk[k].init_test = True
            blk[k].hold_state = hold_state

    def release_state(blk, flags=None, outlvl=0):
        for k in blk.keys():
            blk[k].hold_state = not blk[k].hold_state


@declare_process_block_class("TestStateBlock", block_class=SBlockBase)
class StateTestBlockData(StateBlockData):
    CONFIG = ConfigBlock(implicit=True)

    def build(self):
        super(StateTestBlockData, self).build()

        self.flow_vol = Var(initialize=20, units=units.m**3/units.s)
        self.flow_mol_phase_comp = Var(self.params.phase_list,
                                       self.params.component_list,
                                       initialize=2,
                                       units=units.mol/units.s)
        self.test_var = Var(initialize=1)
        self.pressure = Var(initialize=1e5, units=units.Pa)
        self.temperature = Var(initialize=300, units=units.K)

        self.enth_mol = Var(initialize=10000, units=units.J/units.mol)

        self.gibbs_mol_phase_comp = Var(self.params.phase_list,
                                        self.params.component_list,
                                        initialize=50,
                                        units=units.J/units.mol)
        self.entr_mol = Var(initialize=1000, units=units.J/units.mol/units.K)

        self.mole_frac_phase_comp = Var(self.params.phase_list,
                                        self.params.component_list,
                                        initialize=0.5)

    def get_material_flow_terms(b, p, j):
        if b.config.parameters.basis_switch == 2:
            u = units.kg/units.s
        else:
            u = units.mol/units.s
        return b.test_var*u

    def get_material_density_terms(b, p, j):
        if b.config.parameters.basis_switch == 2:
            u = units.kg/units.m**3
        else:
            u = units.mol/units.m**3
        return b.test_var*u

    def get_enthalpy_flow_terms(b, p):
        return b.test_var*units.J/units.s

    def get_energy_density_terms(b, p):
        return b.test_var*units.J/units.m**3

    def model_check(self):
        self.check = True

    def get_material_flow_basis(b):
        if b.config.parameters.basis_switch == 1:
            return MaterialFlowBasis.molar
        elif b.config.parameters.basis_switch == 2:
            return MaterialFlowBasis.mass
        else:
            return MaterialFlowBasis.other

    def default_material_balance_type(self):
        if self.params.default_balance_switch == 1:
            return MaterialBalanceType.componentPhase
        else:
            raise NotImplementedError

    def default_energy_balance_type(self):
        if self.params.default_balance_switch == 1:
            return EnergyBalanceType.enthalpyTotal
        else:
            raise NotImplementedError

    def define_state_vars(self):
        return {"component_flow_phase": self.flow_mol_phase_comp,
                "temperature": self.temperature,
                "pressure": self.pressure}


@declare_process_block_class("ReactionParameterTestBlock")
class _ReactionParameterBlock(ReactionParameterBlock):
    def build(self):
        super(_ReactionParameterBlock, self).build()

        self.rate_reaction_idx = Set(initialize=["r1", "r2"])
        self.equilibrium_reaction_idx = Set(initialize=["e1", "e2"])

        self.rate_reaction_stoichiometry = {("r1", "p1", "c1"): 1,
                                            ("r1", "p1", "c2"): 1,
                                            ("r1", "p2", "c1"): 1,
                                            ("r1", "p2", "c2"): 1,
                                            ("r2", "p1", "c1"): 1,
                                            ("r2", "p1", "c2"): 1,
                                            ("r2", "p2", "c1"): 1,
                                            ("r2", "p2", "c2"): 1}
        self.equilibrium_reaction_stoichiometry = {
                                            ("e1", "p1", "c1"): 1,
                                            ("e1", "p1", "c2"): 1,
                                            ("e1", "p2", "c1"): 1,
                                            ("e1", "p2", "c2"): 1,
                                            ("e2", "p1", "c1"): 1,
                                            ("e2", "p1", "c2"): 1,
                                            ("e2", "p2", "c1"): 1,
                                            ("e2", "p2", "c2"): 1}

        self._reaction_block_class = ReactionBlock

        # Attribute to switch flow basis for testing
        self.basis_switch = 1

    @classmethod
    def define_metadata(cls, obj):
        obj.add_default_units({'time': units.s,
                               'length': units.m,
                               'mass': units.kg,
                               'amount': units.mol,
                               'temperature': units.K})

    @classmethod
    def get_required_properties(self):
        return {}


class RBlockBase(ReactionBlockBase):
    def initialize(blk, outlvl=0, optarg=None,
                   solver=None, state_vars_fixed=False):
        for k in blk.keys():
            blk[k].init_test = True


@declare_process_block_class("ReactionBlock", block_class=RBlockBase)
class ReactionBlockData(ReactionBlockDataBase):
    CONFIG = ConfigBlock(implicit=True)

    def build(self):
        super(ReactionBlockData, self).build()

        self.reaction_rate = Var(["r1", "r2"],
                                 units=units.mol/units.m**3/units.s)

        self.dh_rxn = {"r1": 10*units.J/units.mol,
                       "r2": 20*units.J/units.mol,
                       "e1": 30*units.J/units.mol,
                       "e2": 40*units.J/units.mol}

    def model_check(self):
        self.check = True

    def get_reaction_rate_basis(b):
        if b.config.parameters.basis_switch == 1:
            return MaterialFlowBasis.molar
        elif b.config.parameters.basis_switch == 2:
            return MaterialFlowBasis.mass
        else:
            return MaterialFlowBasis.other
