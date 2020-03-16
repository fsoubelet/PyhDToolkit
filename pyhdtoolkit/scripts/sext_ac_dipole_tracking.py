"""
Created on 2020.02.27
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 utility to launch a series of MAD-X simlations with the proper parameters,
call the appropriate python scripts on the outputs and organise the results.

Made to be ran with the OMC conda environment, and ran directly for the commandline.

A pair of examples
==================

Running with kicks in the horizontal plane only, for two sigma values:
python path/to/sext_ac_dipole_tracking.py --planes horizontal --mask /path/to/kick/mask.mask --type kick --sigmas 5 10

Running with free oscillations in both planes succesively, for many offset values:
python path/to/sext_ac_dipole_tracking.py --planes horizontal vertical --mask /path/to/offset/mask.mask --type amp \
-- sigmas 5 10 15 20
"""
import argparse
import sys
from pathlib import Path

from fsbox import logging_tools
from fsbox.contexts import timeit

from pyhdtoolkit.utils import CommandLine

OMC_ENV_PYTHON = Path().home() / "anaconda3" / "envs" / "OMC" / "bin" / "python"
TBT_CONVERTER_SCRIPT = Path().home() / "Repositories" / "Work" / "omc3" / "omc3" / "tbt_converter.py"

LEVELS_DICT: dict = {
    "debug": logging_tools.DEBUG,
    "info": logging_tools.INFO,
    "warning": logging_tools.WARNING,
    "error": logging_tools.ERROR,
}
LOGGER = logging_tools.get_logger(__name__)


class ACDipoleGrid:
    """
    Algorithm as a class to run the simulations and organize the outputs.
    """

    def __init__(self):
        self.grid_output_dir: Path = Path(f"grid_outputs")
        self.mask_files_dir: Path = self.grid_output_dir / "mask_files"
        self.outputdata_dir: Path = self.grid_output_dir / "outputdata_dirs"
        self.trackfiles_dir: Path = self.grid_output_dir / "trackfiles"
        self.trackfiles_planes: dict = {
            "horizontal": self.grid_output_dir / "trackfiles" / "X",
            "vertical": self.grid_output_dir / "trackfiles" / "Y",
        }
        self.run_planes: list = _parse_args()[1]
        self.sigmas: list = sorted(_parse_args()[0])
        self.template_file: Path = Path(_parse_args()[2])
        with self.template_file.open("r") as template:
            self.template_str: str = template.read()

    def _check_input_sanity(self) -> None:
        """
        Make sure there are no duplicates in the provided sigma values,
        because that will mess up in a long time and you will cry.
        """
        if len(self.sigmas) != len(set(self.sigmas)):
            LOGGER.error(
                f"There is a duplicate in the provided sigma values, which will cause a failure later. Aborting."
            )
            sys.exit()

    def _create_output_dirs(self) -> None:
        """Will create the proper output dirs if they don't exist already."""
        if not self.grid_output_dir.is_dir():
            LOGGER.debug(f"Creating directory '{self.grid_output_dir}'")
            self.grid_output_dir.mkdir()
        if not self.mask_files_dir.is_dir():
            LOGGER.debug(f"Creating directory '{self.mask_files_dir}'")
            self.mask_files_dir.mkdir()
        if not self.outputdata_dir.is_dir():
            LOGGER.debug(f"Creating directory '{self.outputdata_dir}'")
            self.outputdata_dir.mkdir()
        if not self.trackfiles_dir.is_dir():
            LOGGER.debug(f"Creating directory '{self.trackfiles_dir}'")
            self.trackfiles_dir.mkdir()
        if not self.trackfiles_planes["horizontal"].is_dir():
            LOGGER.debug(f"Creating directory '{self.trackfiles_planes['horizontal']}'")
            self.trackfiles_planes["horizontal"].mkdir()
        if not self.trackfiles_planes["vertical"].is_dir():
            LOGGER.debug(f"Creating directory '{self.trackfiles_planes['vertical']}'")
            self.trackfiles_planes["vertical"].mkdir()
        else:
            LOGGER.error(f"Output directories already present, you may want to move those.")
            sys.exit()

    def track_kicks_for_plane(self, kick_plane: str = None) -> None:
        """Run MAD-X simulations with AC dipole tracking for the given plane, and handle outputs."""
        if kick_plane not in ("horizontal", "vertical"):
            raise ValueError(
                f"Plane parameter should be one of 'horizontal', 'vertical' but {kick_plane} was provided."
            )
        plane_letter = "x" if kick_plane == "horizontal" else "y"

        with timeit(
            lambda spanned: LOGGER.info(f"Tracked all amplitudes for {kick_plane} kicks in {spanned:.4f} seconds")
        ):
            for kick_in_sigma in self.sigmas:
                print("")
                # Dict is set to give the wanted kick value (in sigmas) only in the given plane, and a small initial
                # offset only in the other plane to later on compute the tune (smallest offset so that GUI doesn't cry)
                # Do NOT kick both planes as cross-terms will mess up the exactitude of the observed detuning!
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
                filename_to_write = Path(f"sext_ac_dipole_tracking_{kick_in_sigma}_sigma_{plane_letter}_kick")
                mask_file = create_script_file(
                    self.template_str, values_replacing_dict=replace_dict, filename=str(filename_to_write)
                )
                run_madx_mask(mask_file)
                _move_mask_file_after_running(mask_file_path=mask_file, mask_files_dir=self.mask_files_dir)
                _rename_madx_outputs(
                    kick_in_sigma=kick_in_sigma, outputdata_dir=self.outputdata_dir, plane=plane_letter
                )
                _convert_trackone_to_sdds()
                _move_trackone_sdds(
                    kick_in_sigma=kick_in_sigma, trackfiles_dir=self.trackfiles_planes[kick_plane], plane=plane_letter
                )

    def track_amplitude_for_plane(self, kick_plane: str = None) -> None:
        """Run MAD-X simulations tracking with amplitude initial for the given plane, and handle outputs."""
        if kick_plane not in ("horizontal", "vertical"):
            raise ValueError(
                f"Plane parameter should be one of 'horizontal', 'vertical' but {kick_plane} was provided."
            )
        plane_letter = "x" if kick_plane == "horizontal" else "y"

        with timeit(
            lambda spanned: LOGGER.info(f"Tracked all amplitudes for {kick_plane} offsets in {spanned:.4f} seconds")
        ):
            for kick_in_sigma in self.sigmas:
                print("")
                # There is not so much guarantee of hitting the same amplitudes than with kicks because I haven't
                # checked yet, since free oscillations tracking is fast, better do a lot of values.
                action_var_value = kick_in_sigma
                amplitudes_dict = (
                    {"%(AMPLX_VALUE)s": action_var_value, "%(AMPLY_VALUE)s": 0.5}
                    if kick_plane == "horizontal"
                    else {"%(AMPLX_VALUE)s": 0.5, "%(AMPLY_VALUE)s": action_var_value}
                )
                filename_to_write = Path(f"initial_amplitude_tracking_{kick_in_sigma}_sigma_{plane_letter}_kick")
                mask_file = create_script_file(
                    self.template_str, values_replacing_dict=amplitudes_dict, filename=str(filename_to_write)
                )
                run_madx_mask(mask_file)
                _move_mask_file_after_running(mask_file_path=mask_file, mask_files_dir=self.mask_files_dir)
                _rename_madx_outputs(
                    kick_in_sigma=kick_in_sigma, outputdata_dir=self.outputdata_dir, plane=plane_letter
                )
                _convert_trackone_to_sdds()
                _move_trackone_sdds(
                    kick_in_sigma=kick_in_sigma, trackfiles_dir=self.trackfiles_planes[kick_plane], plane=plane_letter
                )


def main() -> None:
    """
    Run the whole process: create a class instance, simulate for horizontal and vertical kicks, return.
    :return: nothing.
    """
    _set_logger_level()

    simulations = ACDipoleGrid()
    simulations._check_input_sanity()
    simulations._create_output_dirs()

    sim_type = _parse_args()[3]
    if sim_type == "kick":
        LOGGER.info(f"Planes to kick then track on are: {simulations.run_planes}")
        LOGGER.info(f"Kick values to compute are (in bunch sigmas): {simulations.sigmas}")
        for plane in simulations.run_planes:
            simulations.track_kicks_for_plane(kick_plane=plane)
    if sim_type == "amp":
        LOGGER.info(f"Planes to offset then track on are: {simulations.run_planes}")
        LOGGER.info(f"Registered initial amplitudes for tracking are (in bunch sigmas): {simulations.sigmas}")
        for plane in simulations.run_planes:
            simulations.track_amplitude_for_plane(kick_plane=plane)


# ---------------------- Public Utilities ---------------------- #


def run_madx_mask(mask_file: Path) -> None:
    """
    Run madx on the provided file.
    :param mask_file: a `pathlib.Path` object with the mask file location.
    :return: nothing.
    """
    LOGGER.debug(f"Running madx on script: '{mask_file}'")
    exit_code, std_out = CommandLine.run(f"madx {mask_file}")
    std_out = std_out.decode()  # Default considers 'utf-8', can be different depending on your system.
    if exit_code != 0:  # Dump madx log in case of failure so we can see where it went wrong.
        LOGGER.warning(f"MAD-X command self-killed with exit code: {exit_code}")
        log_dump = Path(f"failed_madx_returnedcode_{exit_code}.log")
        with log_dump.open("w") as logfile:
            logfile.write(std_out)
        LOGGER.warning(f"The standard output has been dumped to file 'failed_command_{exit_code}.logfile'.")


def create_script_file(template_as_str: str = None, values_replacing_dict: dict = None, filename: Path = None) -> Path:
    """
    Create new script file from template with the appropriate values.
    :param template_as_str: string content of your template mask file.
    :param values_replacing_dict: keys to find and values to replace them with in the template.
    :param filename: the `pathlib.Path` object for the file in which to write the script.
    :return: Nothing.
    """
    string_mask = _create_script_string(template_as_str, values_replacing_dict)
    written_file = _write_script_to_file(string_mask, filename)
    return written_file


# ---------------------- Private Utilities ---------------------- #


def _convert_trackone_to_sdds() -> None:
    """
    Run the omc3 tbt_converter script on trackone output of MAD-X. Will also cleanup the `converter` and
    'stats' files left by tbt_converter afterwards.
    :return: nothing.
    """
    if not Path("trackone").is_file():
        LOGGER.error(f"Tried to call 'tbt_converter' without a 'trackone' file present, aborting")
        sys.exit()

    LOGGER.debug(f"Running '{TBT_CONVERTER_SCRIPT}' on 'trackone' file")
    CommandLine.run(f"{OMC_ENV_PYTHON} {TBT_CONVERTER_SCRIPT} --file trackone --outputdir . --tbt_datatype trackone")
    LOGGER.debug(f"Removing trackone file 'trackone'")
    Path("trackone").unlink()

    LOGGER.debug(f"Removing outputs of 'tbt_converter'")
    Path("stats.txt").unlink()
    for tbt_output_file in list(Path(".").glob("converter_*")):
        tbt_output_file.unlink()


def _create_script_string(template_as_string: str, values_replacing_dict: dict = None) -> str:
    """
    For each key in the provided dict, will replace it in the template scripts
    with the corresponding dict value.
    :param template_as_string: then string content of your template mask file.
    :param values_replacing_dict: pairs of key, value to find and replace in the template string.
    :return: the new script string.
    """
    script_string: str = template_as_string
    for key, value in values_replacing_dict.items():
        script_string = script_string.replace(str(key), str(value))
    return script_string


def _move_mask_file_after_running(mask_file_path: Path, mask_files_dir: Path) -> None:
    """
    Move the mask file after being done running it with MAD-X.
    :param mask_file_path: `pathlib.Path` object to the file.
    :param mask_files_dir: `pathlib.Path` object to the directory to move it to.
    :return: nothing.
    """
    LOGGER.debug(f"Moving mask file to 'grid_outputs'")
    mask_file_path.rename(f"{mask_files_dir}/{mask_file_path}")


def _move_trackone_sdds(kick_in_sigma: str, trackfiles_dir: Path, plane: str) -> None:
    """
     Call after running omc3's `tbt_converter` on the `trackone` output by MAD-X, will move the resulting
    `trackone.sdds` to the `trackfiles_dir`, with a naming reflecting the ac dipole kick strength.
    :param kick_in_sigma: the AC dipole kick value (in sigma) for which you ran your simulation.
    :param trackfiles_dir: the folder in which to store all sdds trackone files.
    :param plane: the plane on which ac dipole provided the kick, should be `x` or `y`.
    :return: nothing.
    """
    if str(plane) not in ("x", "y"):
        raise ValueError(f"Plane parameter should be one of 'x', 'y' but {plane} was provided.")
    LOGGER.debug(f"Moving trackone sdds file to 'grid_outputs'")
    track_sdds_file = Path("trackone.sdds")
    track_sdds_file.rename(f"{trackfiles_dir}/trackone_{kick_in_sigma}_sigma_{plane}.sdds")


def _parse_args():
    """Simple argument parser to make life easier in the command-line."""
    parser = argparse.ArgumentParser(description="Running MAD-X AC dipole trackings for you.")
    parser.add_argument(
        "-s",
        "--sigmas",
        dest="sigmas",
        nargs="+",
        default=[1, 2],
        type=float,
        help="Different amplitude values (in bunch sigma) for the AC dipole kicks, defaults to [1, 2].",
    )
    parser.add_argument(
        "-p",
        "--planes",
        dest="planes",
        nargs="+",
        default=["horizontal"],
        type=str,
        help="Planes for which to kick, possible values are 'horizontal' and 'vertical', defaults to 'horizontal'.",
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
        dest="type",
        default="kick",
        type=str,
        help="Type of simulations to run, either 'kick' for AC dipole kick or 'amp' for initial amplitude tracking. "
        "Defaults to 'kick'.",
    )
    parser.add_argument(
        "-l",
        "--logs",
        dest="log_level",
        default="info",
        type=str,
        help="The base console logging level. Can be 'debug', 'info', 'warning' and 'error'. Defaults to 'info'.",
    )
    options = parser.parse_args()
    return options.sigmas, options.planes, options.template, options.type, options.log_level


def _rename_madx_outputs(kick_in_sigma: str, outputdata_dir: Path, plane: str) -> None:
    """
    Call after running MAD-X on your mask, will move the 'Outpudata' created by MAD-X to the proper place.
    :param kick_in_sigma: the AC dipole kick value (in sigma) for which you ran your simulation.
    :param outputdata_dir: the folder in which to store all successive `Outputdata`.
    :param plane: the plane on which ac dipole provided the kick, should be `x` or `y`.
    :return: Nothing, just moves things around.
    """
    if str(plane) not in ("x", "y"):
        raise ValueError(f"Plane parameter should be one of 'x', 'y' but {plane} was provided.")
    madx_outputs = Path("Outputdata")
    LOGGER.debug(f"Moving MAD-X outputs to 'grid_outputs'")
    madx_outputs.rename(f"{outputdata_dir}/Outputdata_{kick_in_sigma}_sigma_{plane}")


def _set_logger_level():
    """Simple function to update the logger console base level from commandline arguments."""
    global LOGGER
    log_level = _parse_args()[4]
    LOGGER = logging_tools.get_logger(__name__, level_console=LEVELS_DICT[log_level])


def _write_script_to_file(script_as_string: str, filename: str) -> Path:
    """
    Create a new file with the provided script, and return the location.
    :param script_as_string: the script string to write to file.
    :param filename: the file name to use.
    :return: the `pathlib.Path` object to the created file.
    """
    file_path = Path(filename + ".mask")
    LOGGER.debug(f"Creating new mask file '{file_path}'")
    with file_path.open("w") as script:
        script.write(script_as_string)
    return file_path


if __name__ == "__main__":
    main()
