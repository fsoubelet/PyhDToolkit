"""
.. _optics-rdt:

Resonance Driving Terms Utilities
---------------------------------

Module implementing utilities for the handling of
resonance driving terms.
"""


def rdt_to_order_and_type(rdt: int | str) -> str:
    """
    .. versionadded:: 1.5.0

    Decompose the input RDT into its four various components
    and return the type of RDT (normal or skew) and its order.

    Parameters
    ----------
    rdt : int | str
        The RDT to decompose.

    Returns
    -------
    str
        A string with the type and magnet order of
        the provided RDT.

    Examples
    --------

        .. code-block:: python

            rdt_to_order_and_type(1001)
            # Output: 'skew_quadrupole'

        .. code-block:: python

            rdt_to_order_and_type("2002")
            # Output: 'normal_octupole'
    """
    j, k, l, m = map(int, str(rdt))  # noqa: E741
    rdt_type = "normal" if (l + m) % 2 == 0 else "skew"
    orders = {
        1: "dipole",
        2: "quadrupole",
        3: "sextupole",
        4: "octupole",
        5: "decapole",
        6: "dodecapole",
        7: "tetradecapole",
        8: "hexadecapole",
    }
    return f"{rdt_type}_{orders[j + k + l + m]}"


def determine_rdt_line(rdt: int | str, plane: str) -> tuple[int, int, int]:
    """
    .. versionadded:: 1.5.0

    Find the given line to look for in the spectral analysis
    of the given plane that corresponds to the given RDT.

    Parameters
    ----------
    rdt : int | str
        The RDT to look for.
    plane : str
        The plane to look for the RDT in.

    Returns
    -------
    tuple[int, int, int]
        A tuple of three integers representing the line to
        look for in the spectral analysis. For instance,
        f1001 corresponds to the line (0, 1, 0) in the X
        plane which means the line located at 1 * Qy = Qy.

    Examples
    --------

        .. code-block:: python

            determine_rdt_line(1001, "X")
            # Output: (0, 1, 0)
            # Line at 1 * Qy in the X spectrum.

        .. code-block:: python

            determine_rdt_line("2002", "Y")
            # Output: (-2, 3, 0)
            # Line at 3 * Qy - 2 * Qx in the Y spectrum.
    """
    j, k, l, m = map(int, str(rdt))  # noqa: E741
    lines = {"X": (1 - j + k, m - l, 0), "Y": (k - j, 1 - l + m, 0)}
    return lines[plane]
