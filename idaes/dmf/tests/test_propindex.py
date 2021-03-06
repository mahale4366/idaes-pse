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
Tests for idaes.dmf.propindex module.
"""
# stdlib
import logging
import shutil
import sys

# third-party
import pytest

# package
import idaes
from idaes.dmf import propindex
from idaes.dmf import DMF
from idaes.dmf import resource
from idaes.util.system import mkdtemp

# for testing
from .util import init_logging
from . import for_propindex

__author__ = "Dan Gunter <dkgunter@lbl.gov>"

if sys.platform.startswith("win"):
    pytest.skip("skipping DMF tests on Windows", allow_module_level=True)

init_logging()
_log = logging.getLogger(__name__)


@pytest.mark.unit
def test_dmfvisitor():
    with pytest.raises(TypeError):
        propindex.DMFVisitor("o_O", "a")
    propindex.DMFVisitor("o_O")


@pytest.fixture
def tmpd():
    d = mkdtemp(prefix="test_propindex_", suffix=".idaes")
    yield d
    shutil.rmtree(d)


@pytest.fixture
def testdmf(tmpd):
    dmf = DMF(path=tmpd, create=True)
    return dmf


@pytest.mark.unit
def test_index_property_metadata(testdmf):
    propindex.index_property_metadata(
        testdmf, pkg=idaes.dmf, expr=".*IndexMePlease[0-9]", exclude_testdirs=False
    )
    # Check the resource
    for rsrc in testdmf.find():
        assert rsrc.v[rsrc.TYPE_FIELD] == resource.TY_CODE
        # print('@@ GOT RESOURCE:\n{}'.format(rsrc.v))


@pytest.mark.unit
def test_index_multiple_versions(testdmf):
    v1, v2, v3 = "1.0.0", "6.6.6", "9.9.0"
    # index initial version
    propindex.index_property_metadata(
        testdmf,
        pkg=idaes.dmf,
        expr=".*IndexMePlease[0-9]",
        exclude_testdirs=False,
        default_version=v1,
    )
    # index again
    propindex.index_property_metadata(
        testdmf,
        pkg=idaes.dmf,
        expr=".*IndexMePlease[0-9]",
        exclude_testdirs=False,
        default_version=v2,
    )
    # check that we now have two resources, and
    # a relation between them
    rlist = list(testdmf.find({}))
    assert len(rlist) == 2
    rcodes = [r.v["codes"][0] for r in rlist]
    if rcodes[0]["version"][:3] == ("6", "6", "6"):
        first, second = 1, 0
    else:
        first, second = 0, 1

    # Debugging only
    # print('CODES:')
    # print(' - first -')
    # print(rcodes[first])
    # print(rlist[first].v['relations'])
    # print(' - second -')
    # print(rcodes[second])
    # print(rlist[second].v['relations'])

    # Each resource has 1 relation
    assert len(rlist[first].v["relations"]) == 1
    assert len(rlist[second].v["relations"]) == 1
    first_rel = rlist[first].v["relations"][0]
    second_rel = rlist[second].v["relations"][0]
    # First resource is pointed at by second
    assert first_rel[resource.RR_ROLE] == resource.RR_OBJ
    assert first_rel[resource.RR_PRED] == resource.PR_VERSION
    assert first_rel[resource.RR_ID] == rlist[second].id
    # Second resource points at first
    assert second_rel[resource.RR_ROLE] == resource.RR_SUBJ
    assert second_rel[resource.RR_PRED] == resource.PR_VERSION
    assert second_rel[resource.RR_ID] == rlist[first].id

    # Add the same version
    propindex.index_property_metadata(
        testdmf,
        pkg=idaes.dmf,
        expr=".*IndexMePlease[0-9]",
        exclude_testdirs=False,
        default_version=v2,
    )
    # check that we still have two resources
    rlist = list(testdmf.find({}))
    assert len(rlist) == 2

    # Now add another version
    propindex.index_property_metadata(
        testdmf,
        pkg=idaes.dmf,
        expr=".*IndexMePlease[0-9]",
        exclude_testdirs=False,
        default_version=v3,
    )
    # check that we now have three resources
    rlist = list(testdmf.find({}))
    assert len(rlist) == 3
    # check that we have 0 <--> 1 <--> 2
    # first sort by version and save that in the 'indexes' array
    indexes = [(r.v["codes"][0]["version"], i) for i, r in enumerate(rlist)]
    indexes.sort()
    # pull out relations into 'rel' array, in version order
    rel = [rlist[indexes[i][1]].v["relations"] for i in range(3)]
    # check first resource's relations
    assert len(rel[0]) == 1
    # 0 <-- 1
    assert rel[0][0][resource.RR_ID] == rlist[indexes[1][1]].id
    assert rel[0][0][resource.RR_ROLE] == resource.RR_OBJ
    # check second resource's relations
    assert len(rel[1]) == 2
    for j in range(2):
        if rel[1][j][resource.RR_ROLE] == resource.RR_SUBJ:
            # 1 --> 0
            assert rel[1][j][resource.RR_ID] == rlist[indexes[0][1]].id
        else:
            # 1 <-- 2
            assert rel[1][j][resource.RR_ID] == rlist[indexes[2][1]].id
            assert rel[1][j][resource.RR_ROLE] == resource.RR_OBJ
    # check third resource's relations
    assert len(rel[2]) == 1
    # 2 --> 1
    assert rel[2][0][resource.RR_ID] == rlist[indexes[1][1]].id
    assert rel[2][0][resource.RR_ROLE] == resource.RR_SUBJ

