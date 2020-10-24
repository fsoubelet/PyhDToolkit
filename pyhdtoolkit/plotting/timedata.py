import html.parser

from datetime import date, datetime
from typing import List

import dateutil.parser
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import requests

from dateutil.relativedelta import relativedelta
from loguru import logger
from matplotlib.patches import Polygon

from pyhdtoolkit.plotting.settings import PLOT_PARAMS

plt.rcParams.update(PLOT_PARAMS)
WEEKDAYS: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@logger.catch
def calendar_heatmap(
    axis: matplotlib.axes.Axes,
    data: np.ndarray,
    year: int,
    origin: str = "upper",
    cmap: str = "RdYlBu",
) -> None:
    """
    Plots the data as a heatmap on a Github-like calendar type of plot.

    Args:
        axis (matplotlib.axes.Axes): an existing  matplotlib.axis `Axes` object to act on.
        data (np.ndarray): the data to plot, as a number of occurences for each day.
        year (int): the year for which the data has to be plotted.
        origin (str): the bound to use to start counting weekdays, either upper or lower.
            Defaults to 'upper'.
        cmap (str): the color map to use for the heatmap. Defaults to 'RdYlBu'.
    """
    logger.info("Creating calendar heatmap")
    logger.trace("Setting axis parameters")
    axis.tick_params("x", length=0, labelsize="medium", which="major")
    axis.tick_params("y", length=0, labelsize="x-small", which="major")

    xticks, xlabels = [], []
    start = datetime(year, 1, 1).weekday()
    data = _prepare_data(start, data)

    for month in range(1, 13):
        first_day = datetime(year, month, 1)
        last_day = first_day + relativedelta(months=1, days=-1)
        logger.trace(f"Preparing polygon area for {first_day.strftime('%B')} {year}")

        x0: int = (int(first_day.strftime("%j")) + start - 1) // 7
        x1: int = (int(last_day.strftime("%j")) + start - 1) // 7
        xticks.append(x0 + (x1 - x0 + 1) / 2)
        xlabels.append(first_day.strftime("%b"))

        poly = _prepare_polygon(first_day, last_day, origin)
        axis.add_artist(poly)

    logger.trace("Finishing up axis settings")
    axis.set_xticks(xticks)
    axis.set_xticklabels(xlabels)
    axis.set_yticks(0.5 + np.arange(7))
    ylabels = WEEKDAYS if origin.lower() == "lower" else WEEKDAYS[::-1]
    axis.set_yticklabels(ylabels)
    axis.set_title(f"{year}", weight="semibold")

    logger.trace("Mapping data")
    axis.imshow(
        data,
        extent=[0, 54, 0, 7],
        zorder=10,
        vmin=np.nanmin(data),
        vmax=np.nanmax(data),
        cmap=cmap,
        origin=origin,
        # alpha=0.75,
    )


@logger.catch
def _prepare_data(start: int, data: np.ndarray) -> np.ndarray:
    """
    Prepares a ready-to-use in `calendar_heatmap` data array from the initially provided data. The
    returned data array is guaranteed to have the proper shape for a full year, and includes np.nan
    values wherever the initial data does not provide any.

    Args:
        start (int): int value of the weekday for the first day of the year the data is for.
        data (np.ndarray): the data to plot, as a number of occurences for each day.

    Returns:
        A prepared numpy array for the data.
    """
    logger.trace("Preparing data for calendar heatmap")
    print(f"DATA SHAPE: {data.shape}")
    print(f"START: {start}")

    _data = np.zeros(data.shape) * np.nan
    _data[start : start + len(data)] = data
    return _data.reshape(54, 7).T


def _prepare_polygon(
    first_day: datetime, last_day: datetime, origin: str
) -> matplotlib.patches.Polygon:
    """
    Make the calculation for the coordinates of the Polygon corners, based on the first and
    last day of a month to plot, and the origin setting.

    Args:
        first_day (datetime): datetime object for the first day of the month.
        last_day(datetime): datetime object for the last day of the month.
        origin (str): the bound to use to start counting weekdays, either upper or lower.

    Returns:
        The Polygon object.
    """
    start: int = datetime(first_day.year, 1, 1).weekday()

    if origin.lower() not in ("lower", "upper"):
        logger.error(f"The origin must be one of 'upper' or 'lower', but '{origin}' was given")
        raise ValueError("Invalid origin value")

    logger.trace("Preparing Polygon artist corners")
    y0: int = first_day.weekday() if origin.lower() == "lower" else 6 - first_day.weekday()
    y1: int = last_day.weekday() if origin.lower() == "lower" else 6 - last_day.weekday()
    x0: int = (int(first_day.strftime("%j")) + start - 1) // 7
    x1: int = (int(last_day.strftime("%j")) + start - 1) // 7

    if origin.lower() == "lower":
        polygon_corners = [
            (x0, y0),
            (x0, 7),
            (x1, 7),
            (x1, y1 + 1),
            (x1 + 1, y1 + 1),
            (x1 + 1, 0),
            (x0 + 1, 0),
            (x0 + 1, y0),
        ]
    else:
        polygon_corners = [
            (x0, y0 + 1),
            (x0, 0),
            (x1, 0),
            (x1, y1),
            (x1 + 1, y1),
            (x1 + 1, 7),
            (x0 + 1, 7),
            (x0 + 1, y0 + 1),
        ]

    logger.trace("Creating polygon")
    return Polygon(
        polygon_corners, edgecolor="black", facecolor="None", linewidth=1, zorder=20, clip_on=False,
    )


def _github_contributions(year: int, user: str = "fsoubelet") -> np.ndarray:
    """
    Fetch the Github contribution data for the given user in the given year. See how contributions
    are counted here: https://docs.github.com/en/free-pro-team@latest/github/setting-up-and-managing-your-github-profile/why-are-my-contributions-not-showing-up-on-my-profile

    Args:
        year (int): the year to request the data for.
        user (str): the github username to get the contribution data for. Defaults to mine.

    Returns:
        A numpy array with the number of contributions for each day in the year.
    """
    url: str = f"https://github.com/users/{user}/contributions?to={year}-12-31"
    contents = str(requests.get(url).content)

    n = 1 + (date(year, 12, 31) - date(year, 1, 1)).days
    data = -np.zeros(n, dtype=int)

    class HTMLParser(html.parser.HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "rect":
                data_ = {key: value for (key, value) in attrs}
                date_ = dateutil.parser.parse(data_["data-date"])
                count = int(data_["data-count"])
                day = date_.timetuple().tm_yday - 1
                if count > 0:
                    data[day] = count

    parser = HTMLParser()
    parser.feed(contents)
    return data
