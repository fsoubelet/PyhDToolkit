import matplotlib.pyplot as plt
import numpy as np
import pytest

from matplotlib.testing.decorators import image_comparison

from pyhdtoolkit.plotting.helpers import AnnotationsPlotter


class TestAnnotationsPlotter:
    @image_comparison(
        baseline_images=["arrow_label"],
        remove_text=True,
        extensions=["png", "pdf"],
        savefig_kwarg={"dpi": 300},
    )
    @pytest.mark.xfail(reason="Can't figure out matplotlib testing yet.")
    def test_set_arrow_label(self):
        fig = plt.figure(figsize=(12, 7))
        ax = fig.add_subplot()
        ax.scatter(0, 0)
        ax.set_xlim((-1, 2))
        ax.set_ylim((-1, 2))
        AnnotationsPlotter.set_arrow_label(
            axis=ax,
            label="Test label on a test point",
            color="b",
            arrow_position=(0, 0),
            label_position=(1, 1),
            arrow_arc_rad=-0.2,
        )


# This is directly from the matplotlib library, surely that should work, right??
@image_comparison(
    baseline_images=["contour_uneven"], extensions=["png"], remove_text=True, style="mpl20"
)
@pytest.mark.xfail(reason="Can't figure out matplotlib testing yet.")
def test_contour_uneven():
    z = np.arange(24).reshape(4, 6)
    fig, axs = plt.subplots(1, 2)
    ax = axs[0]
    cs = ax.contourf(z, levels=[2, 4, 6, 10, 20])
    fig.colorbar(cs, ax=ax, spacing="proportional")
    ax = axs[1]
    cs = ax.contourf(z, levels=[2, 4, 6, 10, 20])
    fig.colorbar(cs, ax=ax, spacing="uniform")
