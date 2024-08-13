import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from pyhdtoolkit.plotting.crossing import plot_two_lhc_ips_crossings

# Forcing non-interactive Agg backend so rendering is done similarly across platforms during tests
mpl.use("Agg")


@pytest.mark.mpl_image_compare(tolerance=35, style="default", savefig_kwargs={"dpi": 200})
def test_plot_crossing_schemes_ip15(_cycled_lhc_sequences):

    madx = _cycled_lhc_sequences
    figure = plt.figure(figsize=(18, 11))
    plot_two_lhc_ips_crossings(madx, first_ip=1, second_ip=5)
    return figure


@pytest.mark.mpl_image_compare(tolerance=35, style="default", savefig_kwargs={"dpi": 200})
def test_plot_crossing_schemes_ip28_no_highlight(_cycled_lhc_sequences):

    madx = _cycled_lhc_sequences
    figure = plt.figure(figsize=(18, 11))
    plot_two_lhc_ips_crossings(madx, first_ip=2, second_ip=8, highlight_mqx_and_mbx=False)
    return figure
