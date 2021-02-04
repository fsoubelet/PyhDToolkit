import pathlib

from pyhdtoolkit.optics import HorizontalAmplitudeDetuning, VerticalAmplitudeDetuning

CURRENT_DIR = pathlib.Path(__file__).parent
INPUTS_DIR = CURRENT_DIR / "inputs"
TWISS_FILE = INPUTS_DIR / "twiss_for_ampdet.tfs"


class TestHorizontalAmpDet:
    """
    Only testing that some final results are good, considering if anything in between goes wrong the
    end result will be way off. A MAD-X run has been performed and created the twiss file
    loaded to run the tests. The values used as reference for testing have been obtained through
    PTC normal anharmonicities.
    """

    detuner = HorizontalAmplitudeDetuning(TWISS_FILE)
    jx = 0  # the horizontal action variable for the reference run, known at runtime
    jy = 0  # the vertical action variable for the reference run, known at runtime

    def test_first_order_direct_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.dqx_djx() == 0

    def test_second_order_direct_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.d2qx_djx2() == 0

    def test_first_order_cross_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.dqx_djy() == 0

    def test_second_order_cross_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.d2qx_djy2() == 0

    def test_second_order_mixed_term(self):
        print(self.detuner.twiss_file.absolute())
        assert self.detuner.d2qx_djxdjy() == 0

    def test_total_horizontal_detuning(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.dqx(self.jx, self.jy)


class TestVerticalAmpDet:
    """
    Only testing that some final results are good, considering if anything in between goes wrong the
    end result will be way off. A MAD-X run has been performed and created the twiss file
    loaded to run the tests. The values used as reference for testing have been obtained through
    PTC normal anharmonicities.
    """

    detuner = VerticalAmplitudeDetuning(TWISS_FILE)
    jx = 0  # the horizontal action variable for the reference run, known at runtime
    jy = 0  # the vertical action variable for the reference run, known at runtime

    def test_first_order_direct_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.dqy_djy() == 0

    def test_second_order_direct_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.d2qy_djy2() == 0

    def test_first_order_cross_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.dqy_djx() == 0

    def test_second_order_cross_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.d2qy_djx2() == 0

    def test_second_order_mixed_term(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.d2qy_djxdjy() == 0

    def test_total_horizontal_detuning(self):
        print(self.detuner.twiss_file.absolute())
        # assert self.detuner.dqy(self.jx, self.jy)
