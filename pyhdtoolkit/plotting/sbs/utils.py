"""
.. _plotting-sbs-utils:

Segment-by-Segment Utilities
----------------------------

Utility functions to help in the plotting of Segment-by-Segment results.
"""
import tfs

from loguru import logger

# ----- General Purpose SbS Helpers ----- #


def find_ip_s_from_segment_start(segment_df: tfs.TfsDataFrame, model_df: tfs.TfsDataFrame, ip: int) -> float:
    """
    Finds the S-offset of the IP from the start of segment by comparing the S-values for the elements in the model.

    Args:
        segment_df (tfs.TfsDataFrame): A `~tfs.TfsDataFrame` of the segment-by-segment result for the given segment.
        model_df (tfs.TfsDataFrame): The `~tfs.TfsDataframe` of the model's TWISS, usually **twiss_elements.dat**.
        ip (int): The ``LHC`` IP number.

    Returns:
        The S-offset of the IP from the BPM at the start of segment.

    Example:
        .. code-block:: python

            >>> ip_offset_in_segment = find_ip_s_from_segment_start(
            ...     segment_df=sbsphaseext_IP1, model_df=twiss_elements, ip=1
            )
    """
    logger.debug(f"Determining location of IP{ip:d} from the start of segment.")
    first_element: str = segment_df.NAME.to_numpy()[0]
    first_element_s_in_model = model_df[model_df.NAME == first_element].S.to_numpy()[0]
    ip_s_in_model = model_df[model_df.NAME == f"IP{ip:d}"].S.to_numpy()[0]

    # Handle case where IP segment is cut and by end of sequence and the IP is at beginning of machine
    if ip_s_in_model < first_element_s_in_model:
        # Distance to end of sequence + distance from start to IP s
        logger.debug("IP{ip:d} segment seems cut off by end of sequence, looping around to determine IP location")
        distance = (model_df.S.to_numpy().max() - first_element_s_in_model) + ip_s_in_model
    else:  # just the difference
        distance = ip_s_in_model - first_element_s_in_model
    return distance


# ----- Coupling Helpers ----- #


def determine_default_coupling_ylabel(rdt: str, component: str) -> str:
    """
    Creates the ``LaTeX``-compatible label for the Y-axis based on the given coupling *rdt* and its *component*.

    Args:
        rdt (str): The name of the coupling resonance driving term, either ``F1001`` or ``F1010``.
            Case insensitive.
        component (str): Which component of the RDT is considered, either ``ABS``, ``RE`` or ``IM``,
            for absolute value or real / imaginary part, respectively. Case insensitive.

    Returns:
        The label string.

    Example:
        .. code-block:: python

            >>> coupling_label = determine_default_coupling_ylabel(rdt="f1001", component="RE")
    """
    logger.debug(f"Determining a default label for the {component.upper()} component of coupling {rdt.upper()}.")
    assert rdt.upper() in ("F1001", "F1010")
    assert component.upper() in ("ABS", "RE", "IM")

    if component.upper() == "ABS":
        opening = closing = "|"
    elif component.upper() == "RE":
        opening, closing = r"\Re ", ""
    else:
        opening, closing = r"\Im ", ""

    rdt_latex = r"f_{1001}" if rdt.upper() == "F1001" else r"f_{1010}"
    return r"$" + opening + rdt_latex + closing + r"$"


# ----- Phase Helpers ----- #


def determine_default_phase_ylabel(plane: str) -> str:
    """
    Creates the ``LaTeX``-compatible label for the phase Y-axis based on the given *plane*.

    Args:
        plane (str): The plane of the phase, either ``X`` or ``Y``. Case insensitive.

    Returns:
        The label string.

    Example:
        .. code-block:: python

            >>> phase_label = determine_default_phase_ylabel(plane="X")
    """
    logger.debug(f"Determining a default label for the {plane.upper()} phase plane.")
    assert plane.upper() in ("X", "Y")

    beginning = r"\Delta "
    term = r"\phi_{x}" if plane.upper() == "X" else r"\phi_{y}"
    return r"$" + beginning + term + r"$"
