"""
Created on 2019.12.09
:author: Felix Soubelet

A module providing two classes to execute functions + arguments couples through either a multiprocessing approach,
or a multithreading approach.

Here are a few tidbits to keep in mind:
- There can only be one thread running at any given time in a python process. The GIL makes sure of that.
- Multiprocessing is parallelism. Multithreading is concurrency.
- Multiprocessing is for increasing speed. Multithreading is for hiding latency.
- Multiprocessing is best for computations. Multithreading is best for IO.
- If you have CPU heavy tasks, use multiprocessing with n_process = n_cores and never more. Never.
- If you have IO heavy tasks, use multithreading with n_threads = m * n_cores with m a number bigger than 1 that you
can tweak on your own. Try many values and choose the one with the best speedup because there isn’t a general rule.
For instance the default value of m in ThreadPoolExecutor is set to 5 I think is quite random.
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


class MultiProcessor:
    """
    A class to easily wrap a multi-processing context manager call to a function.
    Reminder: multiprocessing is good for cpu-heavy tasks.
    Usage:
        Processor = MultiProcessor()
        results_one_tuple_per_run = Processor.execute_function(
            func=your_cpu_heavy_function, func_args=list_of_args_for_each_call, n_processes=some_int_up_to_you,
        )
    """

    @staticmethod
    def execute_function(func, func_args: list, n_processes: int) -> list:
        """
        Executes the function with the provided arguments as multiple processes.
        Do not give fire up more processes than you have core! Never!
        :param func: the function to call.
        :param func_args: list of the different parameters for each call. If you function takes more than one
        parameters, wrap them up in tuples, e.g. [(params, run, one), (params, run, two), (params, run, three)]
        :param n_processes: the number of processes to fire up. No more than your number of cores!
        :return: a list of tuples, each tuples being the returned value(s) of your function for the given call,
        for instance [(results, run, one), (results, run, two), (results, run, three)].
        """
        with ProcessPoolExecutor(n_processes) as ex:
            res = ex.map(func, func_args)
        return list(res)


class MultiThreader:
    """
    A class to easily wrap a multi-threading context manager call to a function.
    Reminder: multithreading is good for IO-heavy tasks.
    Usage:
        Processor = MultiProcessor()
        results_one_tuple_per_run = Processor.execute_function(
            func=your_io_heavy_function, func_args=list_of_args_for_each_call, n_processes=some_int_up_to_you,
        )
    """

    @staticmethod
    def execute_function(func, func_args, n_threads):
        """
        Executes the function with the provided arguments as multiple threads.
        Remember there is no point of having more threads than the number calls to be executed, the excess threads
        would be idle and you'd lose the time spent to fire them up.
        :param func: the function to call.
        :param func_args: list of the different parameters for each call. If you function takes more than one
        parameters, wrap them up in tuples, e.g. [(params, run, one), (params, run, two), (params, run, three)]
        :param n_threads: the number of threads to fire up.
        :return: a list of tuples, each tuples being the returned value(s) of your function for the given call,
        for instance [(results, run, one), (results, run, two), (results, run, three)].
        """
        with ThreadPoolExecutor(n_threads) as ex:
            res = ex.map(func, func_args)
        return list(res)
