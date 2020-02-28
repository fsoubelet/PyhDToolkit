"""
Created on 2020.02.27
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a Python3 utility to launch a series of MAD-X simlations with the proper parameters,
call the appropriate python scripts on the outputs and organise the results.

Made to be ran with the OMC conda environment.

Should:
 - [X] Get values from commandline and run for all (sigmax=[...] with sigmay=1 and vice versa)
 - [X] Read template, and create new file with adapted parameter values.
 - [X] Call MAD-X on this file.
 - [X] Rename the outputdata folder with the run params and move it to a global result folder.
 - [X] Call tbt_converter on the output 'trackone' file, rename the outputed sdds and move it to the appropriate folder.
"""

import argparse
from pathlib import Path

from fsbox import logging_tools
from fsbox.contexts import timeit

from pyhdtoolkit.utils import CommandLine

OMC_PYTHON = Path().home() / "anaconda3" / "envs" / "OMC" / "bin" / "python"
TBT_CONVERTER_SCRIPT = Path().home() / "Repositories" / "Work" / "omc3" / "omc3" / "tbt_converter.py"
MY_AFS_WORKDIR = Path("/afs/cern.ch/work/f/fesoubel/public").absolute()
TEMPLATE_FILE = MY_AFS_WORKDIR / "MADX_scripts" / "AC_dipole_tracking" / "template.mask"

with TEMPLATE_FILE.open("r") as f:
    TEMPLATE_STR: str = f.read()

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
        self.sigmas: list = _parse_args()

    def _create_output_dirs(self):
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
        LOGGER.debug(f"Output directories already present, they were not created")

    def run_kicks_for_plane(self, kick_plane: str = None):
        """Run MAD-X simulations for the given plane, and handle outputs."""
        if kick_plane not in ("horizontal", "vertical"):
            raise ValueError(
                f"Plane parameter should be one of 'horizontal', 'vertical' but {kick_plane} was provided."
            )
        plane_letter = "x" if kick_plane == "horizontal" else "y"

        with timeit(lambda spanned: LOGGER.info(f"Tracked all amplitudes for {kick_plane} kicks in {spanned:.6f}")):
            for kick_in_sigma in self.sigmas:
                sigma_dict = (
                    {"%(SIGMAX_VALUE)s": kick_in_sigma, "%(SIGMAY_VALUE)s": 1}
                    if kick_plane == "horizontal"
                    else {"%(SIGMAX_VALUE)s": 1, "%(SIGMAY_VALUE)s": kick_in_sigma}
                )
                filename_to_write = Path(f"sext_ac_dipole_tracking_{kick_in_sigma}_sigma_{plane_letter}_kick")
                mask_file = create_script_file(values_replacing_dict=sigma_dict, filename=str(filename_to_write))
                run_madx_mask(mask_file)
                _move_mask_file_after_running(mask_file_path=mask_file, mask_files_dir=self.mask_files_dir)
                _rename_madx_outputs(
                    kick_in_sigma=kick_in_sigma, outputdata_dir=self.outputdata_dir, plane=plane_letter
                )
                _convert_trackone_to_sdds()
                _move_trackone_sdds(kick_in_sigma=kick_in_sigma, trackfiles_dir=self.trackfiles_dir, plane=plane_letter)


def main():
    """
    Run the whole process: create a class instance, simulate for horizontal and vertical kicks, return.
    :return: nothing.
    """
    simulations = ACDipoleGrid()
    simulations._create_output_dirs()
    LOGGER.info(f"Values for AC dipole kicks (in sigmas) are: {simulations.sigmas}")

    simulations.run_kicks_for_plane(kick_plane="horizontal")
    simulations.run_kicks_for_plane(kick_plane="vertical")


# ---------------------- Public Utilities ---------------------- #


def run_madx_mask(mask_file: Path) -> None:
    """
    Run madx on the provided file.
    :param mask_file: a `pathlib.Path` object with the mask file location.
    :return:
    """
    # print(f"Command would be: 'madx {mask_file}'")
    _, _ = CommandLine.run(f"madx {mask_file}")


def create_script_file(values_replacing_dict: dict = None, filename: Path = None) -> Path:
    """
    Create new script file from template with the appropriate values.
    :param values_replacing_dict: keys to find and values to replace them with in the template.
    :param filename: the `pathlib.Path` object for the file in which to write the script.
    :return: Nothing.
    """
    string_mask = _create_script_string(values_replacing_dict)
    written_file = _write_script_to_file(string_mask, filename)
    return written_file


# ---------------------- Private Utilities ---------------------- #


def _convert_trackone_to_sdds() -> None:
    """
    Run the omc3 tbt_converter script on trackone output of MAD-X. Will also cleanup the `converter` file left
    by tbt_converter afterwards.
    :return: nothing.
    """
    if not Path("trackone").is_file():
        LOGGER.error(f"Tried to call tbt_converter without a 'trackone' file present, aborting")
        raise OSError(f"No Trackone file present in current working directory.")
    CommandLine.run(f"{OMC_PYTHON} {TBT_CONVERTER_SCRIPT} --file trackone --outputdir . --tbt_datatype trackone")
    Path("trackone").unlink()
    LOGGER.debug(f"Removed trackone file 'trackone'")

    Path("stats.txt").unlink()
    for tbt_output_file in list(Path(".").glob("converter_*")):
        tbt_output_file.unlink()
    LOGGER.debug(f"Removed outputs of 'tbt_converter'")


def _create_script_string(values_replacing_dict: dict = None) -> str:
    """
    For each key in the provided dict, will replace it in the template scripts
    with the corresponding dict value.
    :param values_replacing_dict: pairs of key, value to find and replace in the template string.
    :return: the new script string.
    """
    script_string: str = TEMPLATE_STR
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
    track_sdds_file = Path("trackone.sdds")
    track_sdds_file.rename(f"{trackfiles_dir}/trackone_{kick_in_sigma}_sigma_{plane}.sdds")


def _parse_args():
    """Simple argument parser to make life easier in the command-line."""
    parser = argparse.ArgumentParser(description="Running the beta-beating script.")
    parser.add_argument(
        "-s",
        "--sigmas",
        dest="sigmas",
        nargs="+",
        default=[1, 2, 3],
        type=float,
        help="Different amplitude values (in bunch sigma) to which to kick with AC dipole.",
    )
    options = parser.parse_args()
    return options.sigmas


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
    madx_outputs.rename(f"{outputdata_dir}/Outputdata_{kick_in_sigma}_sigma_{plane}")


def _write_script_to_file(script_as_string: str, filename: str) -> Path:
    """
    Create a new file with the provided script, and return the location.
    :param script_as_string: the script string to write to file.
    :param filename: the file name to use.
    :return: the `pathlib.Path` object to the created file.
    """
    file_path = Path(filename + ".mask")
    with file_path.open("w") as script:
        script.write(script_as_string)
    LOGGER.debug(f"Created new mask file '{file_path}'")
    return file_path


def quick_test():
    # TODO: remove after all is good
    simulations = ACDipoleGrid()
    simulations._create_output_dirs()

    LOGGER.info(f"Values for sigma kicks are: {simulations.sigmas}")

    LOGGER.info(f"For horizontal plane")
    for kick_in_sigma in simulations.sigmas:
        sigma_dict = {"%(SIGMAX_VALUE)s": kick_in_sigma, "%(SIGMAY_VALUE)s": 1}
        mask_file = create_script_file(
            values_replacing_dict=sigma_dict,
            filename=str(Path(f"sext_ac_dipole_tracking_{kick_in_sigma}_sigma_x_kick")),
        )

    LOGGER.info(f"For vertical plane")
    for kick_in_sigma in simulations.sigmas:
        sigma_dict = {"%(SIGMAX_VALUE)s": 1, "%(SIGMAY_VALUE)s": kick_in_sigma}
        mask_file = create_script_file(
            values_replacing_dict=sigma_dict,
            filename=str(Path(f"sext_ac_dipole_tracking_{kick_in_sigma}_sigma_y_kick")),
        )


if __name__ == "__main__":
    main()
    # quick_test()
