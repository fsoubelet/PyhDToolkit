"""
.. _utils-executors:

Executors Utilities
-------------------

A module providing two classes to execute functions + arguments couples through either a
multiprocessing approach, or a multithreading approach. Before using these, here are a few
tidbits to keep in mind:

* There can only be one thread running at any given time in a python process because of the GIL.
* Multiprocessing is parallelism. Multithreading is concurrency.
* Multiprocessing is for increasing speed. Multithreading is for hiding latency.
* Multiprocessing is best for computations. Multithreading is best for IO.
* If you have CPU heavy tasks, use multiprocessing with `n_process = n_cores` and never more. Never.
* If you have IO heavy tasks, use multithreading with `n_threads = m * n_cores` with `m` a number
  bigger than 1 that you can tweak on your own. Try many values and choose the one with the best
  speedup because there isn't a general rule.

For instance the default value of `m` in `~concurrent.futures.ThreadPoolExecutor` is set to 5 which
I think is quite random.
"""

from concurrent import futures
from typing import Callable, List

from loguru import logger


class MultiProcessor:
    """
    A class to easily wrap a multi-processing context manager call to a function.

    .. important::
        * Reminder: multiprocessing is good for cpu-heavy tasks.
        * Reminder: only picklable objects can be executed and returned.

    Example:
        .. code-block:: python

            >>> Processor = MultiProcessor()
            >>> results_one_tuple_per_run = Processor.execute_function(
            ...     func=your_cpu_heavy_function,
            ...     func_args=list_of_args_for_each_call,
            ...     n_processes=some_int_up_to_you,
            ... )
    """

    @staticmethod
    def execute_function(func: Callable, func_args: list, n_processes: int) -> List[tuple]:
        """
        Executes the *function* with the provided arguments *func_args* as multiple processes.

        .. warning::
            Do not fire up more processes than you have cores! Never!

        Args:
            func (Callable): the function to call.
            func_args (list): list of the different parameters for each call. If *function*
                takes more than one parameter, wrap them up in tuples, e.g.:
                `[(params, run, one), (params, run, two), (params, run, three)]`.
            n_processes (int): the number of processes to fire up. No more than your number of
                cores! If *n_processes* is `None` or not given, `~concurrent.futures.ProcessPoolExecutor`
                will default it to the number of processors on the machine.

        Returns:
            A list of tuples, each `tuple` being the returned value(s) of *function* for the given
            call, for instance `[(results, run, one), (results, run, two), (results, run, three)]`.

        Example:
            .. code-block:: python

                >>> MultiProcessor.execute_function(
                ...     func=np.square, func_args=list(range(6)), n_processes=2)
                ... )
                [0, 1, 4, 9, 16, 25]
        """
        logger.debug(f"Starting multiprocessing with {n_processes} processes")
        with futures.ProcessPoolExecutor(n_processes) as ex:
            results = ex.map(func, func_args)
        logger.debug(f"All {n_processes} processes finished")
        return list(results)


class MultiThreader:
    """
    A class to easily wrap a multi-threading context manager call to a function.

    .. important::
        Reminder: multithreading is good for IO-heavy tasks.

    Example:
        .. code-block:: python

            >>> Threader = MultiThreader()
            >>> results_one_tuple_per_run = Threader.execute_function(
            ...     func=your_io_heavy_function,
            ...     func_args=list_of_args_for_each_call,
            ...     n_processes=some_int_up_to_you,
            ... )
    """

    @staticmethod
    def execute_function(func: Callable, func_args: list, n_threads: int) -> List[tuple]:
        """
        Executes the *function* with the provided arguments *func_args* as multiple threads.

        .. note::
            Remember: there is no point of having more threads than the number calls to be
            executed, the excess threads would be idle and you wouldd lose the time spent
            to fire them up.

        Args:
            func (Callable): the function to call.
            func_args (list): list of the different parameters for each call. If *function*
                takes more than one parameter, wrap them up in tuples, e.g.:
                `[(params, run, one), (params, run, two), (params, run, three)]`.
            n_threads (int): the number of threads to fire up. No more than your number of
                tasks. If *n_threads* is `None` or not given, `~concurrent.futures.ThreadPoolExecutor`
                will default it to the number of processors on the machine multiplied by 5,
                assuming that it is often used to overlap I/O instead of CPU work and
                the number of workers should be higher than the number of workers for
                a `~concurrent.futures.ProcessPoolExecutor`.

        Returns:
            A list of tuples, each `tuple` being the returned value(s) of *function* for the given
            call, for instance `[(results, run, one), (results, run, two), (results, run, three)]`.
        """
        logger.debug(f"Starting multithreading with {n_threads} threads")
        with futures.ThreadPoolExecutor(n_threads) as ex:
            results = ex.map(func, func_args)
        logger.debug(f"All {n_threads} threads finished")
        return list(results)
