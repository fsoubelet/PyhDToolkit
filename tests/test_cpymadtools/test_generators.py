import random

import pytest

from pyhdtoolkit.cpymadtools._generators import LatticeGenerator


def test_base_cas_lattice_generation():
    base_cas_lattice = LatticeGenerator.generate_base_cas_lattice()
    assert isinstance(base_cas_lattice, str)
    assert len(base_cas_lattice) == 1493


def test_onesext_cas_lattice():
    onesext_cas_lattice = LatticeGenerator.generate_onesext_cas_lattice()
    assert isinstance(onesext_cas_lattice, str)
    assert len(onesext_cas_lattice) == 2051


def test_oneoct_cas_lattice():
    oneoct_cas_lattice = LatticeGenerator.generate_oneoct_cas_lattice()
    assert isinstance(oneoct_cas_lattice, str)
    assert len(oneoct_cas_lattice) == 2050


def test_tripleterrors_study_reference():
    tripleterrors_study_reference = LatticeGenerator._generate_tripleterrors_study_reference()  # noqa: SLF001
    assert isinstance(tripleterrors_study_reference, str)
    assert len(tripleterrors_study_reference) == 1617


@pytest.mark.parametrize(
    ("randseed", "tferror"),
    [
        ("", ""),
        ("95", "195"),
        ("105038", "0.001"),
        (str(random.randint(0, int(1e7))), str(random.randint(0, int(1e7)))),
        (random.randint(0, int(1e7)), random.randint(0, int(1e7))),
    ],
)
def test_tripleterrors_study_tferror_job(randseed, tferror):
    tripleterrors_study_tferror_job = LatticeGenerator._generate_tripleterrors_study_tferror_job(  # noqa: SLF001
        rand_seed=randseed, tf_error=tferror
    )
    assert isinstance(tripleterrors_study_tferror_job, str)
    assert len(tripleterrors_study_tferror_job) == 2521 + len(str(randseed)) + len(str(tferror))
    assert f"eoption, add, seed = {randseed};" in tripleterrors_study_tferror_job
    assert f"B2r = {tferror};" in tripleterrors_study_tferror_job


@pytest.mark.parametrize(
    ("randseed", "mserror"),
    [
        ("", ""),
        ("95", "195"),
        ("105038", "0.001"),
        (str(random.randint(0, int(1e7))), str(random.randint(0, int(1e7)))),
        (random.randint(0, int(1e7)), random.randint(0, int(1e7))),
    ],
)
def test_tripleterrors_study_mserror_job(randseed, mserror):
    tripleterrors_study_mserror_job = LatticeGenerator._generate_tripleterrors_study_mserror_job(  # noqa: SLF001
        rand_seed=randseed, ms_error=mserror
    )
    assert isinstance(tripleterrors_study_mserror_job, str)
    assert len(tripleterrors_study_mserror_job) == 2384 + len(str(randseed)) + len(str(mserror))
    assert f"eoption, add, seed = {randseed};" in tripleterrors_study_mserror_job
    assert f"ealign, ds := {mserror} * 1E-3 * TGAUSS(GCUTR);" in tripleterrors_study_mserror_job
