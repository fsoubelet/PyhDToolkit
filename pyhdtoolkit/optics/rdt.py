"""
.. _optics-rdt:

Resonance Driving Terms Utilities
-----------------

Module implementing utilities for the handling of resonance driving terms.
"""

from typing import Union, Tuple


def rdt_to_order_and_type(rdt: Union[int, str]) -> str:
    """
    Decompose the input RDT into its four various components
    and return the type of RDT (normal or skew) and its order.

    Args:
        rdt (Union[int, str]): the RDT to decompose.

    Returns:
        A string with the type and (magnet) order of
        the provided RDT.
    """
    j, k, l, m = map(int, str(rdt))  # noqa: E741
    rdt_type = "normal" if (l + m) % 2 == 0 else "skew"
    orders = dict(
        (
            (1, "dipole"),
            (2, "quadrupole"),
            (3, "sextupole"),
            (4, "octupole"),
            (5, "decapole"),
            (6, "dodecapole"),
            (7, "tetradecapole"),
            (8, "hexadecapole"),
        )
    )
    return f"{rdt_type}_{orders[j + k + l + m]}"


def determine_rdt_line(rdt: Union[int, str], plane: str) -> Tuple[int, int, int]:
    """
    Find the given line to look for in the spectral analysis of
    the given plane that corresponds to the given RDT.

    Args:
        rdt (Union[int, str]): the RDT to look for.
        plane (str): the plane to look for the RDT in.

    Returns:
        A tuple of three integers representing the line
        to look for in the spectral analysis. For instance,
        f1001 corresponds to the line (0, 1, 0) in the X plane
        which means the line located at 1 * Qy = Qy.
    """
    j, k, l, m = map(int, str(rdt))  # noqa: E741
    lines = dict(X=(1 - j + k, m - l, 0), Y=(k - j, 1 - l + m, 0))
    return lines[plane]
