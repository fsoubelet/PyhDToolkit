"""
.. _cpymadtools-ptc:

PTC Routines
------------

Module with functions to manipulate ``MAD-X`` ``PTC`` functionality through a
`~cpymad.madx.Madx` object.
"""
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, Union

import pandas as pd
import tfs

from cpymad.madx import Madx
from loguru import logger

from pyhdtoolkit.cpymadtools.utils import get_table_tfs


def get_amplitude_detuning(
    madx: Madx, /, order: int = 2, file: Union[Path, str] = None, fringe: bool = False, **kwargs
) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.7.0

    Calculates amplitude detuning coefficients via ``PTC_NORMAL``, with sensible
    defaults set for other relevant ``PTC`` commands used in the process. The
    result table is returned as a `~tfs.frame.TfsDataFrame`, the headers of which
    are the contents of the internal ``SUMM`` table. This is a heavily refactored
    version of an initial implementation by :user:`Joschua Dilly <joschd>`.

    .. important::
        The default values used for the ``PTC_CREATE_LAYOUT`` command are ``model=3``
        (``SixTrack`` model), ``method=4`` (integration order), ``nst=3`` (number of
        integration steps, aka body slices for elements) and ``exact=True`` (use exact
        Hamiltonian, not an approximated one). These can be provided as keyword
        arguments to override them.

        The ``PTC_NORMAL`` command is explicitely given ``icase=6`` by default to
        enforce 6D calculations (see the
        `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_
        for details), ``no=5`` (map order for derivative evaluation of Twiss parameters),
        ``closedorbit=True`` (triggers closed orbit calculation) and ``normal=True``
        (activate calculation of the Normal Form).

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
            Positional only.
        order (int): maximum derivative order coefficient (only 0, 1 or 2
            implemented in ``PTC``). Defaults to 2.
        file (Union[Path, str]): path to output file. Defaults to `None`.
        fringe (bool): boolean flag to include fringe field effects in the
            calculation. Defaults to ``False``.
        **kwargs: Some parameters for the ``PTC`` universe creation can be given as
            keyword arguments. They are `model`, `method`, `nst` and `exact`. The
            `icase`, `no`, `closed_orbit` and `normal` kwargs can be given for the
            ``PTC_NORMAL`` command. Their default values are listed higher up in this
            docstring. Any remaining keyword argument is transmitted to the
            ``PTC_NORMAL`` command.
    
    Returns:
        A `~tfs.frame.TfsDataframe` with the calculated coefficients.

    Example:
        .. code-block:: python

            >>> ampdet_coeffs = get_amplitude_detuning(madx, order=2, closedorbit=True)

        One can also specify parameters for the ``PTC`` universe and the ``PTC_NORMAL``
        command:

        .. code-block:: python

            >>> tracks_dict = get_amplitude_detuning(
            ...     madx, order=3, model=3, exact=True, icase=5, no=6
            ... )
    """
    if order >= 3:
        logger.error(f"Maximum amplitude detuning order in PTC is 2, but {order:d} was requested")
        raise NotImplementedError("PTC amplitude detuning is not implemented for order > 2")

    logger.debug("Looking for PTC universe parameters in keyword arguments")
    model = kwargs.pop("model", 3)
    method = kwargs.pop("method", 4)
    nst = kwargs.pop("nst", 3)
    exact = kwargs.pop("exact", True)

    logger.debug("Looking for PTC_NORMAL parameters in keyword arguments")
    icase = kwargs.pop("icase", 6)
    no = kwargs.pop("no", 5)
    closed_orbit = kwargs.pop("closed_orbit", True)
    normal = kwargs.pop("normal", True)

    logger.debug("Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=model, method=method, nst=nst, exact=exact)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.trace("Selecting tune orders")
    madx.select_ptc_normal(q1="0", q2="0")
    for ii in range(1, order + 1):  # These are d^iQ/ddp^i
        madx.select_ptc_normal(dq1=f"{ii:d}", dq2=f"{ii:d}")

    # ANH = anharmonicities (ex, ey, deltap), works only with parameters as full strings
    # could be done nicer with permutations ...
    logger.trace("Selecting anharmonicities")
    if order >= 1:
        # madx.select_ptc_normal('anhx=0, 0, 1')  # dQx/ddp
        # madx.select_ptc_normal('anhy=0, 0, 1')  # dQy/ddp
        madx.select_ptc_normal("anhx=1, 0, 0")  # dQx/dex
        madx.select_ptc_normal("anhx=0, 1, 0")  # dQx/dey
        madx.select_ptc_normal("anhy=1, 0, 0")  # dQy/dex
        madx.select_ptc_normal("anhy=0, 1, 0")  # dQy/dey

    if order >= 2:
        # madx.select_ptc_normal('anhx=0, 0, 2')  # d^2Qx/ddp^2
        # madx.select_ptc_normal('anhy=0, 0, 2')  # d^2Qy/ddp^2
        madx.select_ptc_normal("anhx=2, 0, 0")  # d^2Qx/dex^2
        madx.select_ptc_normal("anhx=1, 1, 0")  # d^2Qx/dexdey
        madx.select_ptc_normal("anhx=0, 2, 0")  # d^2Qx/dey^2
        madx.select_ptc_normal("anhy=2, 0, 0")  # d^2Qy/dex^2
        madx.select_ptc_normal("anhy=1, 1, 0")  # d^2Qy/dexdey
        madx.select_ptc_normal("anhy=0, 2, 0")  # d^2Qy/dey^2

    logger.debug("Executing PTC Normal")
    madx.ptc_normal(icase=icase, no=no, closed_orbit=closed_orbit, normal=normal, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name="normal_results")
    dframe.index = range(len(dframe.NAME))  # table has a weird index

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def get_rdts(
    madx: Madx, /, order: int = 4, file: Union[Path, str] = None, fringe: bool = False, **kwargs
) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.7.0

    Calculate the resonance driving terms up to *order* via ``PTC_TWISS``,
    with sensible defaults set for other relevant ``PTC`` commands. The result
    table is returned as a `~tfs.frame.TfsDataFrame`, the headers of which are
    the contents of the internal ``SUMM`` table. This is a heavily refactored
    version of an initial implementation by :user:`Joschua Dilly <joschd>`.

    .. important::
        The default values used for the ``PTC_CREATE_LAYOUT`` command are ``model=3``
        (``SixTrack`` model), ``method=4`` (integration order), ``nst=3`` (number of
        integration steps, aka body slices for elements) and ``exact=True`` (use exact
        Hamiltonian, not an approximated one). These can be provided as keyword
        arguments to override them.

        The ``PTC_TWISS`` command is given ``icase=6`` by default to enforce 6D
        calculations (see the 
        `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_
        for details), and ``normal=True`` to trigger saving the normal form analysis
        results in a table called ``NONLIN`` which will then be available through the
        provided `~cpymad.madx.Madx` instance.

        These default values can be changed through keyword arguments.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
            Positional only.
        order (int): map order for derivative evaluation of Twiss parameters.
            Defaults to 4.
        file (Union[Path, str]): path to output file. Default to `None`.
        fringe (bool): boolean flag to include fringe field effects in the
            calculation. Defaults to `False`.
        **kwargs: Some parameters for the ``PTC`` universe creation can be given as
            keyword arguments. They are `model`, `method`, `nst` and `exact`. The
            `icase` and `normal` ones can be given for the ``PTC_TWISS`` command.
            Their default values are listed higher up in this docstring. Any remaining
            keyword argument is transmitted to the ``PTC_TWISS`` command.

    Returns:
        A `~tfs.frame.TfsDataFrame` with the calculated RDTs.

    Example:
        .. code-block:: python

            >>> rdts_df = get_rdts(madx, order=3, fringe=True)

        One can also specify parameters for the ``PTC`` universe and the ``PTC_TWISS``
        command:

        .. code-block:: python

            >>> tracks_dict = get_rdts(
            ...     madx, order=3, model=3, method=6, nst=3, exact=True, icase=5
            ... )
    """
    logger.debug("Looking for PTC universe parameters in keyword arguments")
    model = kwargs.pop("model", 3)
    method = kwargs.pop("method", 4)
    nst = kwargs.pop("nst", 3)
    exact = kwargs.pop("exact", True)
    
    logger.debug("Looking for PTC_TWISS parameters in keyword arguments")
    icase = kwargs.pop("icase", 6)
    normal = kwargs.pop("normal", True)

    logger.debug("Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=model, method=method, nst=nst, exact=exact)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug("Executing PTC Twiss")
    madx.ptc_twiss(icase=icase, no=order, normal=normal, trackrdts=True, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name="twissrdt", headers_table="ptc_twiss_summary")

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def ptc_twiss(
    madx: Madx,
    /,
    order: int = 4,
    file: Union[Path, str] = None,
    fringe: bool = False,
    table: str = "ptc_twiss",
    **kwargs,
) -> tfs.TfsDataFrame:
    """
    .. versionadded:: 0.12.0

    Calculates the ``TWISS`` parameters according to the :cite:t:`Ripken:optics:1989`
    formalism via ``PTC_TWISS``, with sensible defaults set for other relevant ``PTC``
    commands. The result table is returned as a `~tfs.frame.TfsDataFrame`, the headers
    of which are the contents of the internal ``SUMM`` table.

    This is very similar to the `~.ptc.get_rdts` function as both use ``PTC_TWISS``
    internally, however this function does not track RDTs which makes the calculations
    significantly faster.

    .. important::
        The default values used for the ``PTC_CREATE_LAYOUT`` command are ``model=3``
        (``SixTrack`` model), ``method=4`` (integration order), ``nst=3`` (number of
        integration steps, aka body slices for elements) and ``exact=True`` (use exact
        Hamiltonian, not an approximated one). These can be provided as keyword
        arguments to override them.

        The ``PTC_TWISS`` command is given ``icase=6`` by default to enforce 6D
        calculations (see the 
        `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_
        for details), and ``normal=True`` to trigger saving the normal form analysis
        results in a table called ``NONLIN`` which will then be available through the
        provided `~cpymad.madx.Madx` instance.

        These default values can be changed through keyword arguments.

    Args:
        madx (cpymad.madx.Madx): an instanciated `~cpymad.madx.Madx` object.
            Positional only.
        order (int): map order for derivative evaluation of ``TWISS`` parameters.
            Defaults to 4.
        file (Union[Path, str]): path to output file. Default to `None`.
        fringe (bool): boolean flag to include fringe field effects in the calculation.
            Defaults to `False`.
        table (str): the name of the internal table in which to save the results.
            Defaults to **ptc_twiss**.
        **kwargs: Some parameters for the ``PTC`` universe creation can be given as
            keyword arguments. They are `model`, `method`, `nst` and `exact`. The
            `icase` and `normal` ones can be given for the ``PTC_TWISS`` command.
            Their default values are listed higher up in this docstring. Any remaining
            keyword argument is transmitted to the ``PTC_TWISS`` command.
            
    Returns:
        A `~tfs.frame.TfsDataFrame` with the calculated ``TWISS`` parameters.

    Example:
        .. code-block:: python

            >>> twiss_ptc_df = ptc_twiss(madx, order=3)

        One can also specify parameters for the ``PTC`` universe and the ``PTC_TWISS``
        command:

        .. code-block:: python

            >>> tracks_dict = ptc_twiss(
            ...     madx, order=3, model=3, method=6, nst=3, exact=True, icase=5
            ... )
    """
    logger.debug("Looking for PTC universe parameters in keyword arguments")
    model = kwargs.pop("model", 3)
    method = kwargs.pop("method", 4)
    nst = kwargs.pop("nst", 3)
    exact = kwargs.pop("exact", True)
    
    logger.debug("Looking for PTC_TWISS parameters in keyword arguments")
    icase = kwargs.pop("icase", 6)
    normal = kwargs.pop("normal", True)

    logger.debug("Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=model, method=method, nst=nst, exact=exact)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug("Executing PTC Twiss")
    madx.ptc_twiss(icase=icase, no=order, normal=normal, table=table, **kwargs)
    madx.ptc_end()

    dframe = get_table_tfs(madx, table_name=table, headers_table="ptc_twiss_summary")

    if file:
        logger.debug(f"Exporting results to disk at '{Path(file).absolute()}'")
        tfs.write(file, dframe)

    return dframe


def ptc_track_particle(
    madx: Madx,
    /,
    initial_coordinates: Tuple[float, float, float, float, float, float],
    nturns: int,
    sequence: Optional[str] = None,
    observation_points: Sequence[str] = None,
    onetable: bool = False,
    fringe: bool = False,
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """
    .. versionadded:: 0.12.0

    Tracks a single particle for *nturns* through ``PTC_TRACK``, based on its initial
    coordinates. The use of this function is similar to that of
    `~.track.track_single_particle`.

    .. important::
        The default values used for the ``PTC_CREATE_LAYOUT`` command are ``model=3``
        (``SixTrack`` model), ``method=4`` (integration order), ``nst=3`` (number of
        integration steps, aka body slices for elements) and ``exact=True`` (use exact
        Hamiltonian, not an approximated one). These can be provided as keyword
        arguments to override them.

        The ``PTC_TRACK`` command is given ``ELEMENT_BY_ELEMENT=True`` by default to
        force element by element tracking mode.

        These default values can be changed through keyword arguments.

    .. warning::
        If the *sequence* argument is given a string value, the ``USE`` command will be
        ran on the provided sequence name. This means the caveats of ``USE`` apply, for
        instance the erasing of previously defined errors, orbits corrections etc. In
        this case a warning will be logged but the function will proceed. If `None` is
        given (by default) then the sequence already in use will be the one tracking is
        performed on.

    Args:
        madx (cpymad.madx.Madx): an instantiated cpymad.madx.Madx object.
        initial_coordinates (Tuple[float, float, float, float, float, float]): a tuple
            with the ``X, PX, Y, PY, T, PT`` starting coordinates of the particle to
            track. Defaults to all 0 if `None` given.
        nturns (int): the number of turns to track for.
        sequence (Optional[str]): the sequence to use for tracking. If no value is
            provided, it is assumed that a sequence is already defined and in use,
            and this one will be picked up by ``MAD-X``. Beware of the dangers of
            giving a sequence that will be used by ``MAD-X``, see the warning below
            for more information.
        observation_points (Sequence[str]): sequence of all element names at which to
            ``OBSERVE`` during the tracking.
        onetable (bool): flag to combine all observation points data into a single
            table. Defaults to `False`.
        fringe (bool): boolean flag to include fringe field effects in the calculation.
            Defaults to `False`.
        **kwargs: Some parameters for the ``PTC`` universe creation can be given as
            keyword arguments. They are `model`, `method`, `nst`, `exact` and
            `element_by_element` for the ``PTC_TRACK`` command. Their default values
            are listed higher up in this docstring. Any remaining keyword argument is
            transmitted to the ``PTC_TRACK`` command such as the `CLOSED_ORBIT` flag
            to activate closed orbit calculation before tracking. Refer to the
            `MAD-X manual <http://madx.web.cern.ch/madx/releases/last-rel/madxuguide.pdf>`_
            for options.

    Returns:
        A `dict` with a copy of the track table's dataframe for each defined observation
        point, with as columns the coordinates ``x, px, y, py, t, pt, s and e`` (energy).
        The keys of the dictionary are simply named ``observation_point_1``,
        ``observation_point_2`` etc. The first observation point always corresponds to the
        start of machine, the others correspond to the ones manually defined, in the order
        they are defined in.

        If the user has set ``onetable`` to `True`, only one entry is in the dictionary
        under the key ``trackone`` and it has the combined table as a `~pandas.DataFrame`
        for value.

    Example:
        .. code-block:: python

            >>> tracks_dict = ptc_track_particle(
            ...     madx, nturns=1023, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0)
            ... )

        One can also specify parameters for the ``PTC`` universe:

        .. code-block:: python

            >>> tracks_dict = ptc_track_particle(
            ...     madx, nturns=10, initial_coordinates=(2e-4, 0, 1e-4, 0, 0, 0),
            ...     model=3, method=6, nst=3, exact=True
            ... )
    """
    logger.debug("Performing single particle PTC (thick) tracking")
    start = initial_coordinates if initial_coordinates else [0, 0, 0, 0, 0, 0]
    observation_points = observation_points if observation_points else []

    logger.debug("Looking for PTC universe parameters in keyword arguments")
    model = kwargs.pop("model", 3)
    method = kwargs.pop("method", 4)
    nst = kwargs.pop("nst", 3)
    exact = kwargs.pop("exact", True)
    
    logger.debug("Looking for PTC_TRACK parameters in keyword arguments")
    element_by_element = kwargs.pop("element_by_element", True)

    if isinstance(sequence, str):
        logger.warning(f"Sequence '{sequence}' was provided and will be USEd, beware that this will erase errors etc.")
        logger.debug(f"Using sequence '{sequence}' for tracking")
        madx.use(sequence=sequence)

    logger.debug("Creating PTC universe")
    madx.ptc_create_universe()

    logger.trace("Creating PTC layout")
    madx.ptc_create_layout(model=model, method=method, nst=nst, exact=exact)

    logger.trace("Incorporating MAD-X alignment errors")
    madx.ptc_align()  # use madx alignment errors
    madx.ptc_setswitch(fringe=fringe)

    logger.debug(f"Tracking coordinates with initial X, PX, Y, PY, T, PT of '{initial_coordinates}'")
    madx.command.ptc_start(X=start[0], PX=start[1], Y=start[2], PY=start[3], T=start[4], PT=start[5])

    for element in observation_points:
        logger.trace(f"Setting observation point for tracking with OBSERVE at element '{element}'")
        madx.command.ptc_observe(place=element)

    madx.command.ptc_track(turns=nturns, element_by_element=element_by_element, onetable=onetable, **kwargs)
    madx.ptc_end()

    if onetable:  # user asked for ONETABLE, there will only be one table 'trackone' given back by MAD-X
        logger.debug("Because of option ONETABLE only one table 'TRACKONE' exists to be returned.")
        return {"trackone": madx.table.trackone.dframe()}
    return {
        f"observation_point_{point:d}": madx.table[f"track.obs{point:04d}.p0001"].dframe()
        for point in range(1, len(observation_points) + 2)  # len(observation_points) + 1 for start of
        # machine + 1 because MAD-X starts indexing these at 1
    }
