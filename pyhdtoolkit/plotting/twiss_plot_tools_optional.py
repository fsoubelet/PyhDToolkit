"""
Created on 2019.12.09
:author: Felix Soubelet

This module provides simple tools for working with the output of MAD-X (or cpymadtools) simulations..
"""

import matplotlib
import matplotlib.pyplot as plt

ELEMENT_TO_COLOR: dict = {
    "MB": "blue",  # Bending magnet
    "MQ": "red",  # Quadrupole magnet
    "T": "darkgreen",  # Target/collimator, etc
    "A": "magenta",  # RF
}


def get_element_color(element_name: str) -> str:
    """
    Return standard colors for different machine elements.
    """
    try:
        return ELEMENT_TO_COLOR[element_name]
    except KeyError as error:
        print(f"Unknown element: {element_name}")
        raise error


def draw_thick_element_markers(elements, y_pos, s_min=None, s_max=None, is_symmetric: bool = False) -> None:
    """
    Draw thick markers using the element types produced by TwissTable::sliced_rebuild.
    """
    ax = plt.gca()
    for el in elements:
        s_pos = elements[el]
        if s_min is not None and s_pos[1] < s_min:
            continue
        elif s_max is not None and s_pos[0] > s_max:
            # print "SKIP",sMax,el[1]
            continue

        # print el

        textcolor = get_element_color(el)

        # Type 1 annotation
        # plt.annotate(
        #     '', xy=(sPOS[0], yPOS*0.7), xycoords='data',
        #     xytext=(sPOS[1], yPOS*0.7), textcoords='data',
        #     #arrowprops={'arrowstyle': '<->', 'shrink':0.0},
        #     arrowprops=dict(arrowstyle='<->', shrinkA=0.0,shrinkB=0.0),
        #     color=textcolor)

        # plt.annotate(
        #     el,
        #     xy=(0.5*(sPOS[1]+sPOS[0]), yPOS*0.7), xycoords='data',
        #     xytext=(0, 5), textcoords='offset points',
        #     color=textcolor, ha="center")

        # Type 2 annotation
        if is_symmetric:
            ax.add_patch(
                matplotlib.patches.Rectangle(
                    (s_pos[0], -y_pos * 1.2),
                    s_pos[1] - s_pos[0],
                    y_pos * 2.4,
                    color=textcolor,
                    alpha=0.5,
                    edgecolor="none",
                )
            )
            plt.annotate(
                el,
                xy=(0.5 * (s_pos[1] + s_pos[0]), y_pos),
                xycoords="data",
                xytext=(0, 0),
                textcoords="offset points",
                rotation="vertical",
                color=textcolor,
                va="top",
                ha="center",
            )
        else:
            ax.add_patch(
                matplotlib.patches.Rectangle(
                    (s_pos[0], -y_pos * 1.2),
                    s_pos[1] - s_pos[0],
                    y_pos * 2.4,
                    color=textcolor,
                    alpha=0.5,
                    edgecolor="none",
                )
            )
            plt.annotate(
                el,
                xy=(0.5 * (s_pos[1] + s_pos[0]), y_pos),
                xycoords="data",
                xytext=(0, 0),
                textcoords="offset points",
                rotation="vertical",
                color=textcolor,
                va="top",
                ha="center",
            )


def draw_thin_element_markers(TT, y_pos, s_min=None, s_max=None, skip_list: bool = None) -> None:
    prev_s = -1.0
    for (i, s, name) in zip(range(TT.N), TT.data["S"], TT.data["NAME"]):
        if s_min is not None and s < s_min:
            continue
        elif s_max is not None and s > s_max:
            continue

        if float(TT.data["L"][i]) > 0.0:
            # Thin elements only
            continue
        if ".." in name:
            # Sliced elements, skip
            continue

        # Declutter
        do_skip = False
        for skip in skip_list:
            if name.startswith(skip_list):
                do_skip = True
        if do_skip:
            continue

        if TT.elements is not None and name in TT.elements:
            continue

        if prev_s == s:
            continue
        prev_s = s

        textcolor = get_element_color(name)

        plt.axvline(s, ls="--", color=textcolor)
        plt.text(s, y_pos, name, rotation="vertical", color=textcolor, va="top", ha="right")

        # Print a few selected elements:
        # if name.startswith("TCT") or name.startswith("TAS") or name.startswith("TAN"):
        #     print name, TT.data["S"][i], TT.data["BETX"][i], TT.data["BETY"][i]
