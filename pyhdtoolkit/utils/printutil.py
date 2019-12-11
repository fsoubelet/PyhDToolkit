"""
Created on 2019.12.11
:author: Felix Soubelet (felix.soubelet@cern.ch)

A class utility class to allow me printing text in color, bold, etc.
"""


class PrintModes:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
