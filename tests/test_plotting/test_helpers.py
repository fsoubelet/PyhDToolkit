import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest

from pyhdtoolkit.plotting.utils import (
    _determine_default_sbs_coupling_ylabel,
    draw_confidence_ellipse,
    set_arrow_label,
)

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
mpl.use("Agg")


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_set_arrow_label():
    figure = plt.figure(figsize=(12, 7))
    ax = figure.add_subplot()
    ax.scatter(0, 0)
    ax.set_xlim((-1, 2))
    ax.set_ylim((-1, 2))
    set_arrow_label(
        axis=ax,
        label="Test label on a test point",
        color="b",
        arrow_position=(0, 0),
        label_position=(1, 1),
        arrow_arc_rad=-0.2,
    )
    return figure


def test_confidence_ellipse_fails_on_mismatched_dimensions():
    x = np.array([1, 2, 3])
    y = np.array([1, 2, 3, 4])

    with pytest.raises(ValueError, match="x and y must be the same size"):
        draw_confidence_ellipse(x, y)


def test_default_sbs_coupling_label_raises_on_wrong_component():
    with pytest.raises(ValueError, match=r"Invalid component for coupling RDT."):
        _determine_default_sbs_coupling_ylabel(rdt="f1001", component="NONEXISTANT")
