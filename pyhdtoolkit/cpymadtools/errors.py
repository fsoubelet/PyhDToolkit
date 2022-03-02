"""
.. _cpymadtools-errors:

Errors Assignments
------------------

Module with functions to perform ``MAD-X`` errors setups and manipulations through a `~cpymad.madx.Madx`
object, mainly for LHC and HLLHC machines.
"""
from typing import Dict, List, Sequence

from cpymad.madx import Madx
from loguru import logger

# ----- Constants ----- #

# After number 10 are either MQ or MQT quadrupole elements, which officially belong to the arcs
IR_QUADS_PATTERNS: Dict[int, List[str]] = {
    1: ["^MQXA.1{side}{ip:d}", "^MQXFA.[AB]1{side}{ip:d}"],  # Q1 LHC, Q1A & Q1B HL-LHC
    2: ["^MQXB.[AB]2{side}{ip:d}", "^MQXB.[AB]2{side}{ip:d}"],  # Q2A & Q2B LHC, Q2A & Q2B HL-LHC
    3: ["^MQXA.3{side}{ip:d}", "^MQXFA.[AB]3{side}{ip:d}"],  # Q3 LHC, Q3A & Q3B HL-LHC
    4: ["^MQY.4{side}{ip:d}.B{beam:d}"],  # Q4 LHC & HL-LHC
    5: ["^MQML.5{side}{ip:d}.B{beam:d}"],  # Q5 LHC & HL-LHC
    6: ["^MQML.6{side}{ip:d}.B{beam:d}"],  # Q6 LHC & HL-LHC
    7: ["^MQM.[AB]7{side}{ip:d}.B{beam:d}"],  # Q7A & Q7B LHC & HL-LHC
    8: ["^MQML.8{side}{ip:d}.B{beam:d}"],  # Q8 LHC & HL-LHC
    9: ["^MQM.9{side}{ip:d}.B{beam:d}", "^MQMC.9{side}{ip:d}.B{beam:d}"],  # Q9 3.4m then 2.4m LHC & HL-LHC
    10: ["^MQML.10{side}{ip:d}.B{beam:d}"],  # Q10 4.8m LHC & HL-LHC
}


# ----- Utilites ----- #


def switch_magnetic_errors(madx: Madx, **kwargs) -> None:
    """
    Applies magnetic field orders. This will only work for LHC and HLLHC machines.
    Initial implementation credits go to :user:`Joschua Dilly <joschd>`.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        **kwargs: The setting works through keyword arguments, and several specific
            kwargs are expected. `default` sets global default to this value (defaults to `False`).
            `AB#` sets the default for all of that order, the order being the `#` number. `A#` or
            `B#` sets the default for systematic and random of this id. `A#s`, `B#r`, etc. sets the
            specific value for this given order. In all kwargs, the order # should be in the range
            [1...15], where 1 == dipolar field.

    Examples:

        Set random values for (alsmost) all of these orders:

        .. code-block:: python

            >>> random_kwargs = {}
            >>> for order in range(1, 16):
            ...     for ab in "AB":
            ...         random_kwargs[f"{ab}{order:d}"] = random.randint(0, 20)
            >>> switch_magnetic_errors(madx, **random_kwargs)

        Set a given value for ``B6`` order magnetic errors:

        .. code-block:: python

            >>> switch_magnetic_errors(madx, "B6"=1e-4)
    """
    logger.debug("Setting magnetic errors")
    global_default = kwargs.get("default", False)

    for order in range(1, 16):
        logger.trace(f"Setting up for order {order}")
        order_default = kwargs.get(f"AB{order:d}", global_default)

        for ab in "AB":
            ab_default = kwargs.get(f"{ab}{order:d}", order_default)
            for sr in "sr":
                name = f"{ab}{order:d}{sr}"
                error_value = int(kwargs.get(name, ab_default))
                logger.trace(f"Setting global for 'ON_{name}' to {error_value}")
                madx.globals[f"ON_{name}"] = error_value


def misalign_lhc_ir_quadrupoles(
    madx: Madx,
    ips: Sequence[int],
    beam: int,
    quadrupoles: Sequence[int],
    sides: Sequence[str] = ("r", "l"),
    table: str = "ir_quads_errors",
    **kwargs,
) -> None:
    """
    Apply misalignment errors to IR quadrupoles on a given side of given IPs. In case of a sliced
    lattice, this will misalign all slices of each magnet together. According to the
    `Equipment Codes Main System <https://edms5.cern.ch/cedar/plsql/codes.systems>`_,  those are Q1
    to Q10 included, quads beyond are ``MQ`` or ``MQT`` which are considered arc elements.

    One can find a full example use of the function for tracking in the
    :ref:`LHC IR Errors  <demo-ir-errors>` example gallery.

    .. warning::
        This implementation is only valid for LHC IP IRs, which are 1, 2, 5 and 8. Other IRs have
        different layouts incompatible with this function.

    .. warning::
        One should avoid issuing different errors with several uses of this command as it is unclear to me
        how ``MAD-X`` chooses to handle this internally. Instead, it is advised to give all errors in the same
        command, which is guaranteed to work. See the last provided example below.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ips (Sequence[int]): the interaction point(s) around which to apply errors.
        beam (int): beam number to apply the errors to. Unlike triplet quadrupoles which are single
            aperture, Q4 to Q10 are not and will need this information.
        quadrupoles (Sequence[int]): the number of the quadrupoles to apply errors to.
        sides (Sequence[str]): sides of the IP to apply error on the triplets, either L or R or both.
            Case-insensitive. Defaults to both.
        table (str): the name of the internal table that will save the assigned errors. Defaults to
            'ir_quads_errors'.
        **kwargs: Any keyword argument is given to the ``EALIGN`` command, including the error to apply
            (`DX`, `DY`, `DPSI` etc) as a string, like it would be given directly into ``MAD-X``.

    Examples:

        For systematic ``DX`` misalignment:

        .. code-block:: python

            >>> misalign_lhc_ir_quadrupoles(
            ...     madx, ips=[1], quadrupoles=[1, 2, 3, 4, 5, 6], beam=1, sides="RL", dx="1E-5"
            ... )

        For a tilt distribution centered on 1mrad:

        .. code-block:: python

            >>> misalign_lhc_ir_quadrupoles(
            ...     madx, ips=[5], quadrupoles=[7, 8, 9, 10], beam=1, sides="RL", dpsi="1E-3 + 8E-4 * TGAUSS(2.5)"
            ... )

        For several error types on the elements, here ``DY`` and ``DPSI``:

        .. code-block:: python

            >>> misalign_lhc_ir_quadrupoles(
            ...     madx,
            ...     ips=[1, 5],
            ...     quadrupoles=list(range(1, 11)),
            ...     beam=1,
            ...     sides="RL",
            ...     dy=1e-5,  # ok too as cpymad converts this to a string first
            ...     dpsi="1E-3 + 8E-4 * TGAUSS(2.5)"
            ... )
    """
    if any(ip not in (1, 2, 5, 8) for ip in ips):
        logger.error("The IP number provided is invalid, not applying any error.")
        raise ValueError("Invalid 'ips' parameter")
    if beam and beam not in (1, 2, 3, 4):
        logger.error("The beam number provided is invalid, not applying any error.")
        raise ValueError("Invalid 'beam' parameter")
    if any(side.upper() not in ("R", "L") for side in sides):
        logger.error("The side provided is invalid, not applying any error.")
        raise ValueError("Invalid 'sides' parameter")

    sides = [side.upper() for side in sides]
    logger.trace("Clearing error flag")
    madx.select(flag="error", clear=True)

    logger.debug(f"Applying alignment errors to IR quads '{quadrupoles}', with arguments {kwargs}")
    for ip in ips:
        logger.debug(f"Applying errors for IR{ip}")
        for side in sides:
            for quad_number in quadrupoles:
                for quad_pattern in IR_QUADS_PATTERNS[quad_number]:
                    # Triplets are single aperture and don't need beam information, others do
                    if quad_number <= 3:
                        madx.select(flag="error", pattern=quad_pattern.format(side=side, ip=ip))
                    else:
                        madx.select(flag="error", pattern=quad_pattern.format(side=side, ip=ip, beam=beam))
    madx.command.ealign(**kwargs)

    table = table if table else "etable"  # guarantee etable command won't fail if someone gives `table=None`
    logger.debug(f"Saving assigned errors in internal table '{table}'")
    madx.command.etable(table=table)

    logger.trace("Clearing up error flag")
    madx.select(flag="error", clear=True)


def misalign_lhc_triplets(
    madx: Madx, ip: int, sides: Sequence[str] = ("r", "l"), table: str = "triplet_errors", **kwargs
) -> None:
    """
    Apply misalignment errors to IR triplet quadrupoles on a given side of a given IP. In case of a
    sliced lattice, this will misalign all slices of each magnet together. This is a convenience wrapper
    around the `~.errors.misalign_lhc_ir_quadrupoles` function, see that function's docstring for more
    information.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
        ip (int): the interaction point around which to apply errors.
        sides (Sequence[str]): sides of the IP to apply error on the triplets, either L or R or both.
            Case-insensitive. Defaults to both.
        table (str): the name of the internal table that will save the assigned errors. Defaults to
            `triplet_errors`.
        **kwargs: Any keyword argument is given to the ``EALIGN`` command, including the error to apply
            (`DX`, `DY`, `DPSI` etc) as a string, like it would be given directly into ``MAD-X``.

    Examples:

        A random, gaussian truncated ``DX`` misalignment:

        .. code-block:: python

            >>> misalign_lhc_triplets(madx, ip=1, sides="RL", dx="1E-5 * TGAUSS(2.5)")

        A random, gaussian truncated ``DPSI`` misalignment:

        .. code-block:: python

            >>> misalign_lhc_triplets(madx, ip=5, sides="RL", dpsi="0.001 * TGAUSS(2.5)")
    """
    misalign_lhc_ir_quadrupoles(madx, ips=[ip], beam=None, quadrupoles=(1, 2, 3), sides=sides, table=table, **kwargs)
