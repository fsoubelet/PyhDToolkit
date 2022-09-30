import matplotlib
import matplotlib.pyplot as plt
import pytest

from pyhdtoolkit.plotting.tune import plot_tune_diagram

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
matplotlib.use("Agg")


@pytest.mark.parametrize("max_order", [0, 10, -5])
def test_plot_tune_diagram_fails_on_too_high_order(max_order, caplog):
    with pytest.raises(ValueError):
        plot_tune_diagram(max_order=max_order)

    for record in caplog.records:
        assert record.levelname == "ERROR"


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_tune_diagram():
    """Does not need any input."""
    figure = plt.figure(figsize=(10, 10))
    plot_tune_diagram()
    return figure


@pytest.mark.mpl_image_compare(tolerance=20, style="default", savefig_kwargs={"dpi": 200})
def test_plot_tune_diagram_colored_by_resonance_order():
    figure = plt.figure(figsize=(10, 10))
    plot_tune_diagram(differentiate_orders=True)
    return figure


@pytest.mark.parametrize("figure_title", ["", "Tune Diagram"])
@pytest.mark.parametrize("legend_title", ["Resonance Lines"])
@pytest.mark.parametrize("max_order", [2, 3, 4, 5])
@pytest.mark.parametrize("differentiate", [False, True])
def test_plot_tune_diagram_arguments(figure_title, legend_title, max_order, differentiate):
    figure, ax = plt.subplots(figsize=(10, 10))
    plot_tune_diagram(
        title=figure_title,
        legend_title=legend_title,
        max_order=max_order,
        differentiate_orders=differentiate,
    )
    assert ax.get_title() == figure_title
    assert isinstance(ax.legend().get_title(), matplotlib.text.Text)
