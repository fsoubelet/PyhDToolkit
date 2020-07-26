"""
Script scripts.ac_dipole.sext_ac_dipole_tracking
------------------------------------------------

Created on 2020.02.27
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 utility to launch a series of MAD-X simlations with the proper parameters,
call the appropriate python scripts on the outputs and organise the results.

Made to be ran with the OMC conda environment, and ran directly for the commandline.

A pair of examples
==================

Running with kicks in the horizontal plane only, for two sigma values:
python path/to/sext_ac_dipole_tracking.py --planes horizontal --mask /path/to/kick/mask.mask \
       --type kick --sigmas 5 10

Running with free oscillations in both planes succesively, for many offset values:
python path/to/sext_ac_dipole_tracking.py --planes horizontal vertical \
       --mask /path/to/offset/mask.mask --type amp -- sigmas 5 10 15 20
"""
import argparse
import sys

from pathlib import Path

from loguru import logger

from pyhdtoolkit.utils.cmdline import CommandLine
from pyhdtoolkit.utils.contexts import timeit
from pyhdtoolkit.utils.defaults import LOGURU_FORMAT, OMC_PYTHON_ENV, TBT_CONVERTER_SCRIPT


class ACDipoleGrid:
    """
    Algorithm as a class to run the simulations and organize the outputs.
    """

    def __init__(self) -> None:
        self.grid_output_dir: Path = Path("grid_outputs")
        self.mask_files_dir: Path = self.grid_output_dir / "mask_files"
        self.outputdata_dir: Path = self.grid_output_dir / "outputdata_dirs"
        self.trackfiles_dir: Path = self.grid_output_dir / "trackfiles"
        self.trackfiles_planes: dict = {
            "horizontal": self.grid_output_dir / "trackfiles" / "X",
            "vertical": self.grid_output_dir / "trackfiles" / "Y",
        }
        self.run_planes: list = _parse_arguments().planes
        self.sigmas: list = sorted(_parse_arguments().sigmas)
        self.template_file: Path = Path(_parse_arguments().template)
        with self.template_file.open("r") as template:
            self.template_str: str = template.read()

    def _check_input_sanity(self) -> None:
        """
        Makes sure there are no duplicates in the provided sigma values, because that will mess up
        a long time after launch and you will cry.
        """
        if len(self.sigmas) != len(set(self.sigmas)):
            logger.error(
                "There is a duplicate in the sigma values, which would cause a failure later."
            )
            sys.exit()

    def _create_output_dirs(self) -> None:
        """
        Will create the proper output dirs if they don't exist already.
        """
        if not self.grid_output_dir.is_dir():
            logger.debug(f"Creating directory '{self.grid_output_dir}'")
            self.grid_output_dir.mkdir()
        if not self.mask_files_dir.is_dir():
            logger.debug(f"Creating directory '{self.mask_files_dir}'")
            self.mask_files_dir.mkdir()
        if not self.outputdata_dir.is_dir():
            logger.debug(f"Creating directory '{self.outputdata_dir}'")
            self.outputdata_dir.mkdir()
        if not self.trackfiles_dir.is_dir():
            logger.debug(f"Creating directory '{self.trackfiles_dir}'")
            self.trackfiles_dir.mkdir()
        if not self.trackfiles_planes["horizontal"].is_dir():
            logger.debug(f"Creating directory '{self.trackfiles_planes['horizontal']}'")
            self.trackfiles_planes["horizontal"].mkdir()
        if not self.trackfiles_planes["vertical"].is_dir():
            logger.debug(f"Creating directory '{self.trackfiles_planes['vertical']}'")
            self.trackfiles_planes["vertical"].mkdir()
        else:
            logger.error("Output directories already present, you may want to move those.")
            sys.exit()

    def track_forced_oscillations_for_plane(self, kick_plane: str = None) -> None:
        """
        Run MAD-X simulations with AC dipole tracking for the given plane, and handle outputs.

        Args:
            kick_plane: the name of the plane on which to apply a kick, either 'horizontal'
                        or 'vertical'.

        Returns:
            Nothing, runs simulations and orders the outputs properly.
        """
        if kick_plane not in ("horizontal", "vertical"):
            logger.error(f"Plane parameter {kick_plane} is not a valid value")
            raise ValueError("Plane parameter should be one of 'horizontal' or 'vertical'")

        with timeit(
            lambda spanned: logger.info(
                f"Tracked all amplitudes for {kick_plane} kicks in {spanned:.4f} seconds"
            )
        ):
            for kick_in_sigma in self.sigmas:
                print("")
                # Set the wanted kick value (in sigmas) in the given plane, and a small initial
                # offset in the other (small offset so that harpy doesn't cry and we get tune).
                # Do NOT kick both planes: cross-terms influence the detuning.
                plane_letter = "x" if kick_plane == "horizontal" else "y"
                replace_dict = (
                    {
                        "%(SIGMAX_VALUE)s": kick_in_sigma,
                        "%(SIGMAY_VALUE)s": 0,
                        "%(AMPLX_VALUE)s": 0,
                        "%(AMPLY_VALUE)s": 0.5,
                    }
                    if kick_plane == "horizontal"
                    else {
                        "%(SIGMAX_VALUE)s": 0,
                        "%(SIGMAY_VALUE)s": kick_in_sigma,
                        "%(AMPLX_VALUE)s": 0.5,
                        "%(AMPLY_VALUE)s": 0,
                    }
                )
                filename_to_write = Path(
                    f"sext_ac_dipole_tracking_{kick_in_sigma}_sigma_{plane_letter}_kick"
                )
                mask_file = create_script_file(
                    self.template_str,
                    values_replacing_dict=replace_dict,
                    filename=Path(str(filename_to_write)),
                )
                run_madx_mask(mask_file)
                _move_mask_file_after_running(
                    mask_file_path=mask_file, mask_files_dir=self.mask_files_dir
                )
                _rename_madx_outputs(
                    kick_in_sigma=kick_in_sigma,
                    outputdata_dir=self.outputdata_dir,
                    plane=plane_letter,
                )
                _convert_trackone_to_sdds()
                _move_trackone_sdds(
                    kick_in_sigma=kick_in_sigma,
                    trackfiles_dir=self.trackfiles_planes[kick_plane],
                    plane=plane_letter,
                )

    def track_free_oscillations_for_plane(self, kick_plane: str = None) -> None:
        """
        Run MAD-X simulations with amplitude offset tracking for the given plane, and handle outputs.

        Args:
            kick_plane: the name of the plane on which to apply an offset, either 'horizontal'
                        or 'vertical'.

        Returns:
            Nothing, runs simulations and orders the outputs properly.
        """
        if kick_plane not in ("horizontal", "vertical"):
            logger.error(f"Plane parameter {kick_plane} is not a valid value")
            raise ValueError("Plane parameter should be one of 'horizontal' or 'vertical'")

        with timeit(
            lambda spanned: logger.info(
                f"Tracked all amplitudes for {kick_plane} offsets in {spanned:.4f} seconds"
            )
        ):
            for kick_in_sigma in self.sigmas:
                print("")
                plane_letter = "x" if kick_plane == "horizontal" else "y"
                action_var_value = kick_in_sigma
                amplitudes_dict = (
                    {"%(AMPLX_VALUE)s": action_var_value, "%(AMPLY_VALUE)s": 0.5}
                    if kick_plane == "horizontal"
                    else {"%(AMPLX_VALUE)s": 0.5, "%(AMPLY_VALUE)s": action_var_value}
                )
                filename_to_write = Path(
                    f"initial_amplitude_tracking_{kick_in_sigma}_sigma_{plane_letter}_kick"
                )
                mask_file = create_script_file(
                    self.template_str,
                    values_replacing_dict=amplitudes_dict,
                    filename=Path(str(filename_to_write)),
                )
                run_madx_mask(mask_file)
                _move_mask_file_after_running(
                    mask_file_path=mask_file, mask_files_dir=self.mask_files_dir
                )
                _rename_madx_outputs(
                    kick_in_sigma=kick_in_sigma,
                    outputdata_dir=self.outputdata_dir,
                    plane=plane_letter,
                )
                _convert_trackone_to_sdds()
                _move_trackone_sdds(
                    kick_in_sigma=kick_in_sigma,
                    trackfiles_dir=self.trackfiles_planes[kick_plane],
                    plane=plane_letter,
                )


@logger.catch
def main() -> None:
    """
    Run the whole process: create a class instance, simulate for horizontal and vertical kicks,
    exit.

    Returns:
        Nothing.
    """
    command_line_args = _parse_arguments()
    _set_logger_level(command_line_args.log_level)

    simulations = ACDipoleGrid()
    simulations._check_input_sanity()
    simulations._create_output_dirs()

    sim_type = command_line_args.simulation_type
    if sim_type == "kick":
        logger.info(f"Planes to kick then track on are: {simulations.run_planes}")
        logger.info(f"Kick values to compute are (in bunch sigmas): {simulations.sigmas}")
        for plane in simulations.run_planes:
            simulations.track_forced_oscillations_for_plane(kick_plane=plane)
    elif sim_type == "amp":
        logger.info(f"Planes to offset then track on are: {simulations.run_planes}")
        logger.info(
            f"Registered initial amplitudes for tracking are (in bunch sigmas): {simulations.sigmas}"
        )
        for plane in simulations.run_planes:
            simulations.track_free_oscillations_for_plane(kick_plane=plane)
    else:
        logger.error(f"Simulation type {sim_type} is not a valid value")
        raise ValueError("Simulation type should be one of 'kick' or 'amp'")


# ---------------------- Public Utilities ---------------------- #


def run_madx_mask(mask_file: Path) -> None:
    """
    Run madx on the provided file.

    Args:
        mask_file: a `pathlib.Path` object with the mask file location.

    Returns:
        Nothing.
    """
    logger.debug(f"Running madx on script: '{mask_file}'")
    exit_code, std_out = CommandLine.run(f"madx {mask_file}")
    std_out = (
        std_out.decode()
    )  # Default considers 'utf-8', can be different depending on your system.
    if exit_code != 0:  # Dump madx log in case of failure so we can see where it went wrong.
        logger.warning(f"MAD-X command self-killed with exit code: {exit_code}")
        log_dump = Path(f"failed_madx_returnedcode_{exit_code}.log")
        with log_dump.open("w") as logfile:
            logfile.write(std_out)
        logger.warning(
            f"The standard output has been dumped to file 'failed_command_{exit_code}.logfile'"
        )


def create_script_file(
    template_as_str: str = None, values_replacing_dict: dict = None, filename: Path = None
) -> Path:
    """
    Create new script file from template with the appropriate values.

    Args:
        template_as_str: string content of your template mask file.
        values_replacing_dict: keys to find and values to replace them with in the template.
        filename: the `pathlib.Path` object for the file in which to write the script.

    Returns:
        Nothing.
    """
    string_mask = _create_script_string(template_as_str, values_replacing_dict)
    return _write_script_to_file(string_mask, filename)


# ---------------------- Private Utilities ---------------------- #


def _convert_trackone_to_sdds() -> None:
    """
    Run the omc3 tbt_converter script on trackone output of MAD-X. Will also cleanup the `converter`
    and 'stats' files left by tbt_converter afterwards.

    Returns:
        Nothing.
    """
    if not Path("trackone").is_file():
        logger.error("Tried to call 'tbt_converter' without a 'trackone' file present, aborting")
        sys.exit()

    logger.debug(f"Running '{TBT_CONVERTER_SCRIPT}' on 'trackone' file")
    CommandLine.run(
        f"{OMC_PYTHON_ENV} {TBT_CONVERTER_SCRIPT} --file trackone --outputdir . --tbt_datatype trackone"
    )
    logger.debug("Removing trackone file 'trackone'")
    Path("trackone").unlink()

    logger.debug("Removing outputs of 'tbt_converter'")
    Path("stats.txt").unlink()
    for tbt_output_file in list(Path(".").glob("converter_*")):
        tbt_output_file.unlink()


def _create_script_string(template_as_string: str, values_replacing_dict: dict = None) -> str:
    """
    For each key in the provided dict, will replace it in the template scripts
    with the corresponding dict value.

    Args:
        template_as_string: the string content of your template mask file.
        values_replacing_dict: pairs of key, value to find and replace in the template string.

    Returns:
        The new script string.
    """
    script_string: str = template_as_string
    for key, value in values_replacing_dict.items():
        script_string = script_string.replace(str(key), str(value))
    return script_string


def _move_mask_file_after_running(mask_file_path: Path, mask_files_dir: Path) -> None:
    """
    Move the mask file after being done running it with MAD-X.

    Args:
        mask_file_path: a `pathlib.Path` object with the file location.
        mask_files_dir: a `pathlib.Path` object with the directory to move mask to' location.

    Returns:
        Nothing.
    """
    logger.debug(f"Moving mask file '{mask_file_path}' to directory '{mask_files_dir}'")
    mask_file_path.rename(f"{mask_files_dir}/{mask_file_path}")


def _move_trackone_sdds(kick_in_sigma: str, trackfiles_dir: Path, plane: str) -> None:
    """
    Call after running omc3's `tbt_converter` on the `trackone` output by MAD-X, will move the
    resulting `trackone.sdds` file to the `trackfiles_dir`, with a naming reflecting the ac dipole
    kick strength.

    Args:
        kick_in_sigma: the AC dipole kick value (in sigma) for which you ran your simulation.
        trackfiles_dir: the folder in which to store all sdds trackone files.
        plane: the plane on which ac dipole provided the kick, should be `x` or `y`.

    Returns:
        Nothing.
    """
    if str(plane) not in ("x", "y"):
        logger.error(f"Plane parameter {plane} is not a valid value")
        raise ValueError("Plane parameter should be one of 'x' or 'y'")
    logger.debug(f"Moving trackone sdds file to directory '{trackfiles_dir}'")
    track_sdds_file = Path("trackone.sdds")
    track_sdds_file.rename(f"{trackfiles_dir}/trackone_{kick_in_sigma}_sigma_{plane}.sdds")


def _parse_arguments():
    """
    Simple argument parser to make life easier in the command-line.
    Returns a NameSpace with arguments as attributes.
    """
    parser = argparse.ArgumentParser(description="Running MAD-X AC dipole trackings for you.")
    parser.add_argument(
        "-s",
        "--sigmas",
        dest="sigmas",
        nargs="+",
        default=[1, 2],
        type=float,
        help="Different amplitude values (in bunch sigma) for the AC dipole kicks."
        "Defaults to [1, 2].",
    )
    parser.add_argument(
        "-p",
        "--planes",
        dest="planes",
        nargs="+",
        default=["horizontal"],
        type=str,
        help="Planes for which to kick, possible values are 'horizontal' and 'vertical',"
        "Defaults to 'horizontal'.",
    )
    parser.add_argument(
        "-m",
        "--mask",
        dest="template",
        default="/afs/cern.ch/work/f/fesoubel/public/MADX_scripts/AC_dipole_tracking/ac_kick_track_template.mask",
        type=str,
        help="Location of your MAD-X template mask file to use, defaults to "
        "'/afs/cern.ch/work/f/fesoubel/public/MADX_scripts/AC_dipole_tracking/ac_kick_track_template.mask'.",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="simulation_type",
        default="kick",
        type=str,
        help="Type of simulations to run, either 'kick' for AC dipole kick or 'amp' for free "
        "oscillations. Defaults to 'kick'.",
    )
    parser.add_argument(
        "-l",
        "--logs",
        dest="log_level",
        default="info",
        type=str,
        help="The base console logging level. Can be 'debug', 'info', 'warning' and 'error'."
        "Defaults to 'info'.",
    )
    return parser.parse_args()


def _rename_madx_outputs(kick_in_sigma: str, outputdata_dir: Path, plane: str) -> None:
    """
    Call after running MAD-X on your mask, will move the 'Outpudata' created by MAD-X to the
    proper place.

    Args:
        kick_in_sigma: the AC dipole kick value (in sigma) for which you ran your simulation.
        outputdata_dir: a `pathlib.Path` object with the folder in which to store all successive
                        `Outputdata`'s location.
        plane: the plane on which ac dipole provided the kick, should be `x` or `y`.

    Returns:
        Nothing.
    """
    if str(plane) not in ("x", "y"):
        raise ValueError(f"Plane parameter should be one of 'x', 'y' but {plane} was provided.")
    madx_outputs = Path("Outputdata")
    logger.debug(f"Moving MAD-X outputs to directory '{outputdata_dir}'")
    madx_outputs.rename(f"{outputdata_dir}/Outputdata_{kick_in_sigma}_sigma_{plane}")


def _set_logger_level(log_level: str = "info") -> None:
    """
    Sets the logger level to the one provided at the commandline.

    Default loguru handler will have DEBUG level and ID 0.
    We need to first remove this default handler and add ours with the wanted level.

    Args:
        log_level: string, the default logging level to print out.

    Returns:
        Nothing, acts in place.
    """
    logger.remove(0)
    logger.add(sys.stderr, format=LOGURU_FORMAT, level=log_level.upper())


def _write_script_to_file(script_as_string: str, filename: str) -> Path:
    """
    Create a new file with the provided script, and return the location.

    Args:
        script_as_string:  the script string to write to file.
        filename: the file name to use.

    Returns:
        The `pathlib.Path` object to the created file.
    """
    file_path = Path(filename + ".mask")
    logger.debug(f"Creating new mask file '{file_path}'")
    with file_path.open("w") as script:
        script.write(script_as_string)
    return file_path


if __name__ == "__main__":
    main()
