import matplotlib
import matplotlib.pyplot as plt
import pytest

from pyhdtoolkit.plotting.utils import set_arrow_label

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")


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
