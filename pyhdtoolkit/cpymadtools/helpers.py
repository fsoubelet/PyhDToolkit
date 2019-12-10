"""
Created on 2019.06.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection of functions for performing different common operations on a cpymad.MadX object..
"""


class LatticeMatcher:
    """
    A class with functions to perform MAD-X matchings.
    """

    @staticmethod
    def perform_tune_matching(cpymad_instance, sequence_name, q1_target, q2_target) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will run an additional matching command to reach
        the provided values for tunes.
        :param cpymad_instance: an instanciated `cpymad.MadX` object.
        :param sequence_name: name of the sequence you want to activate for the tune matching.
        :param q1_target: horizontal tune to match to.
        :param q2_target: vertical tune to match to.
        :return: nothing.
        """
        cpymad_instance.input(
            f"""
!MATCHING SEQUENCE
match, sequence={sequence_name};
  vary, name=kqf, step=0.00001;
  vary, name=kqd, step=0.00001;
  global, sequence=CAS3, Q1={q1_target};
  global, sequence=CAS3, Q2={q2_target};
  Lmdif, calls=1000, tolerance=1.0e-21;
endmatch;
twiss;
"""
        )

    @staticmethod
    def perform_chroma_matching(cpymad_instance, sequence_name, dq1_target, dq2_target) -> None:
        """
        Provided with an active Cpymad class after having ran a script, will run an additional matching command to reach
        the provided values for chromaticities.
        :param cpymad_instance: an instanciated `cpymad.MadX` object.
        :param sequence_name: name of the sequence you want to activate for the tune matching.
        :param dq1_target: horizontal chromaticity to match to.
        :param dq2_target: vertical chromaticity to match to.
        :return:
        """
        cpymad_instance.input(
            f"""
!MATCHING SEQUENCE
match, sequence={sequence_name};
  vary, name=ksf, step=0.00001;
  vary, name=ksd, step=0.00001;
  global, sequence=CAS3, dq1={dq1_target};
  global, sequence=CAS3, dq2={dq2_target};
  Lmdif, calls=1000, tolerance=1.0e-21;
endmatch;
twiss;
"""
        )


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
