import math
import multiprocessing
import os
import random
import subprocess
import sys

import pytest

from loguru import logger

from pyhdtoolkit.utils import defaults  # here for coverage
from pyhdtoolkit.utils.cmdline import CommandLine
from pyhdtoolkit.utils.executors import MultiProcessor, MultiThreader
from pyhdtoolkit.utils.operations import (
    ListOperations,
    MiscellaneousOperations,
    NumberOperations,
    StringOperations,
)


def _square(integer: int) -> int:
    return integer ** 2


def _to_str(integer: int) -> str:
    return str(integer)


class TestDefaults:
    def test_logger_config(self, capsys):
        defaults.config_logger()
        message = "This should be in stdout now"
        logger.info(message)
        captured = capsys.readouterr()
        assert message in captured.out

        # This is to get it back as it is by defaults for other tests
        logger.remove()
        logger.add(sys.stderr)


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="Windows is a shitshow for this.",
)
class TestCommandLine:
    def test_check_pid(self):
        assert CommandLine.check_pid_exists(os.getpid()) is True
        assert CommandLine.check_pid_exists(0) is True
        assert (
            CommandLine.check_pid_exists(int(1e6)) is False
        )  # default max PID is 32768 on linux, 99999 on macOS
        with pytest.raises(TypeError):
            CommandLine.check_pid_exists("not_an_integer")

    def test_run_cmd(self):
        assert type(CommandLine.run("echo hello")) is tuple
        assert type(CommandLine.run("echo hello")[1]) is bytes
        assert CommandLine.run("echo hello") == (0, b"hello\n")
        modified_env = os.environ.copy()
        modified_env["TEST_VAR"] = "Check_me_string"
        assert CommandLine.run("echo $TEST_VAR", env=modified_env) == (0, b"Check_me_string\n")
        with pytest.raises(FileNotFoundError):
            CommandLine.run("echo hello", shell=False)

    @pytest.mark.parametrize("sleep_time", list(range(1, 15)))
    def test_run_cmd_timedout(self, sleep_time):
        with pytest.raises(subprocess.TimeoutExpired):
            CommandLine.run(f"sleep {sleep_time}", timeout=0.1)

    @pytest.mark.parametrize("pid", [random.randint(1e6, 5e6) for _ in range(10)])
    def test_terminate_nonexistent_pid(self, pid):
        """Default max PID is 32768 on linux, 99999 on macOS."""
        assert CommandLine.terminate(pid) is False

    @pytest.mark.parametrize("sleep_time", list(range(10, 60)))  # each one will spawn a different process
    def test_terminate_pid(self, sleep_time):
        sacrificed_process = subprocess.Popen(f"sleep {sleep_time}", shell=True)
        assert CommandLine.terminate(sacrificed_process.pid) is True


class TestListOperations:
    @pytest.mark.parametrize(
        "args, result", [([1, 2, 3, 5, 12, 0], True), ([1, 1, 1], False), (list(), True)]
    )
    def test_all_unique(self, args, result):
        assert ListOperations.all_unique(args) is result

    @pytest.mark.parametrize("args, error", [(None, TypeError), (_square, TypeError)])
    def test_all_unique_fails(self, args, error):
        with pytest.raises(error):
            ListOperations.all_unique(args)

    @pytest.mark.parametrize(
        "inputs, function, result",
        [
            ([{"n": 4}, {"n": 2}, {"n": 8}, {"n": 6}], lambda x: x["n"], 5),
            (list(range(10)), lambda x: 2 * x, 9),
            (list(range(10)), lambda x: x, 4.5),
        ],
    )
    def test_average_by(self, inputs, function, result):
        assert ListOperations.average_by(sequence=inputs, function=function) == result

    @pytest.mark.parametrize("inputs, error", [(None, TypeError), ((list(range(10)), None), TypeError)])
    def test_average_by_fails(self, inputs, error):
        with pytest.raises(error):
            ListOperations.average_by(inputs)

    @pytest.mark.parametrize(
        "inputs, filters, results",
        [
            (["beep", "boop", "foo", "bar"], [True, True, False, True], [["beep", "boop", "bar"], ["foo"]],),
            (
                [1, _square, _to_str, "string"],
                [False, True, False, True],
                [[_square, "string"], [1, _to_str]],
            ),
        ],
    )
    def test_bifurcate(self, inputs, filters, results):
        assert ListOperations.bifurcate(inputs, filters) == results

    @pytest.mark.parametrize(
        "inputs, filters, error",
        [
            (["beep", "boop", "foo", "bar", "baz"], None, TypeError),
            (["beep", "boop", "foo", "bar", "baz"], [], IndexError),
            ([["beep", "boop", "foo", "bar"], [True, False, False], IndexError]),
        ],
    )
    def test_bifurcate_fails(self, inputs, filters, error):
        with pytest.raises(error):
            ListOperations.bifurcate(inputs, filters)

    @pytest.mark.parametrize(
        "inputs, func, results",
        [(list(range(5)), lambda x: x % 2 == 0, [[0, 2, 4], [1, 3]]), ([], lambda x: x % 2 == 0, [[], []]),],
    )
    def test_bifurcate_by(self, inputs, func, results):
        assert ListOperations.bifurcate_by(inputs, func) == results

    @pytest.mark.parametrize(
        "array, size, result",
        [
            (list(range(10)), 3, [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]),
            (list(range(10)), 20, list(range(10))),
            (list(), 5, list()),
        ],
    )
    def test_chunk_list(self, array, size, result):
        assert ListOperations.chunk_list(array, size) == result

    @pytest.mark.parametrize(
        "array, size, error",
        [(list(range(10)), 0, ZeroDivisionError), (5, 20, TypeError), ([], "string", TypeError)],
    )
    def test_chunk_list_fails(self, array, size, error):
        with pytest.raises(error):
            ListOperations.chunk_list(array, size)

    @pytest.mark.parametrize(
        "args, result",
        [
            (
                [["a", "b", "c"], [1, 2, 3], [True, False, False]],
                ["a", "b", "c", 1, 2, 3, True, False, False],
            ),
            (
                [["a", "b", "c"], [1, 2, 3], [], [True, False, False]],
                ["a", "b", "c", 1, 2, 3, True, False, False],
            ),
            ([["a", "b", "c"], [1, 2, 3], None, [True, False]], ["a", "b", "c", 1, 2, 3, None, True, False],),
        ],
    )
    def test_deep_flatten(self, args, result):
        assert ListOperations.deep_flatten(args) == result

    @pytest.mark.parametrize(
        "array, func, result",
        [([0, 0, 1, 0], lambda x: x >= 2, True), ([0, 1, 2, 0], lambda x: x >= 2, False)],
    )
    def test_eval_none(self, array, func, result):
        assert ListOperations.eval_none(array, func) is result

    @pytest.mark.parametrize(
        "array, func, result",
        [([0, 1, 2, 0], lambda x: x >= 2, True), ([0, 0, 1, 0], lambda x: x >= 2, False)],
    )
    def test_eval_some(self, array, func, result):
        assert ListOperations.eval_some(array, func) is result

    @pytest.mark.parametrize(
        "element, array, result",
        [
            (0, [0, 1, 3, 5, 7, 3, 9, 0, 0, 5, 3, 2], [0, 7, 8]),
            (0, (0, 1, 3, 5, 7, 3, 9, 0, 0, 5, 3, 2), [0, 7, 8]),
            (2, [2, 2, 2, 2], [0, 1, 2, 3]),
            (5, [], []),
            (0, [1, 2, 3], []),
            ([2], [[1], [2], [3]], [1]),
        ],
    )
    def test_get_indices(self, element, array, result):
        assert ListOperations.get_indices(element, array) == result

    @pytest.mark.parametrize("element, array, error", [(5, None, TypeError)])
    def test_get_indices_fails(self, element, array, error):
        with pytest.raises(error):
            ListOperations.get_indices(element, array)

    @pytest.mark.parametrize(
        "array, func, result",
        [
            (list(range(5)), lambda x: x % 2 == 0, {True: [0, 2, 4], False: [1, 3]}),
            (list(range(5)), lambda x: x >= 2, {True: [2, 3, 4], False: [0, 1]}),
        ],
    )
    def test_groupby(self, array, func, result):
        assert ListOperations.group_by(array, func) == result

    @pytest.mark.parametrize(
        "array, result", [([1, 2, 1], True), ([list(range(10)), False]), ([], False), ([True, True], True)],
    )
    def test_has_duplicates(self, array, result):
        assert ListOperations.has_duplicates(array) is result

    @pytest.mark.parametrize("array, error", [(1, TypeError), (_square, TypeError)])
    def test_has_duplicates_fails(self, array, error):
        with pytest.raises(error):
            ListOperations.has_duplicates(array)

    @pytest.mark.parametrize("args", [(["a", "b", 1, 2, False]), ([_square, 1, "string", True, _to_str])])
    def test_sample(self, args):
        assert ListOperations.sample(args) in args

    @pytest.mark.parametrize(
        "input_list, result",
        [
            ([1, False, "a", 2, "", None, 6, 0], [1, "a", 2, 6]),
            (list(range(1, 10)), list(range(1, 10))),
            ([], []),
            ([0, "", None, False], []),
        ],
    )
    def test_sanitize(self, input_list, result):
        assert ListOperations.sanitize_list(input_list) == result

    @pytest.mark.flaky(max_runs=3, min_passes=1)
    @pytest.mark.parametrize(
        "array",
        [
            ([1, 2, 3, "a", "b", "c", False, True, False]),
            ([True, False, 1, 2, False, ("a", "nested", "tuple")]),
            ([_square, 1, 2, "a_string", "another_string", False, True, None, _to_str]),
        ],
    )
    def test_shuffle_list(self, array):
        shuffled = ListOperations.shuffle(array)
        assert shuffled != array and set(shuffled) == set(array)

    @pytest.mark.parametrize(
        "array, result",
        [
            ([list(range(5)), list(range(5))], [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]),
            ([], []),
            (
                [[1, 2], [None], [True, False], [_square, "string"]],
                [1, 2, None, True, False, _square, "string"],
            ),
        ],
    )
    def test_spread(self, array, result):
        assert ListOperations.spread(array) == result

    @pytest.mark.parametrize(
        "array1, array2, func, result",
        [
            ([2.1, 1.2], [2.3, 3.4], math.floor, [1.2, 3.4]),
            ([2.1, 1.2], [0.5, 1.2], lambda x: x >= 2, [2.1]),
            ([False, True], [True, False], lambda x: x, []),
            (list(range(10)), list(range(10)), math.sqrt, []),
        ],
    )
    def test_symmetric_difference_by(self, array1, array2, func, result):
        assert ListOperations.symmetric_difference_by(array1, array2, func) == result

    @pytest.mark.parametrize(
        "array1, array2, func, error",
        [(list(range(10)), list(range(10)), None, TypeError), (None, [], _square, TypeError)],
    )
    def test_symmetric_difference_by_fails(self, array1, array2, func, error):
        with pytest.raises(error):
            ListOperations.symmetric_difference_by(array1, array2, func)

    @pytest.mark.parametrize(
        "array1, array2, func, result",
        [
            ([2.1], [1.2, 2.3], math.floor, [1.2, 2.1]),
            (["A", "B"], ["a", "c"], str.lower, ["A", "B", "c"]),
            ([], [], None, []),
        ],
    )
    def test_union_by(self, array1, array2, func, result):
        assert ListOperations.union_by(array1, array2, func) == result

    @pytest.mark.parametrize(
        "array1, array2, func, error",
        [(list(range(10)), list(range(10)), None, TypeError), (None, [], _square, TypeError)],
    )
    def test_union_by_fails(self, array1, array2, func, error):
        with pytest.raises(error):
            ListOperations.union_by(array1, array2, func)

    def test_zipper(self):
        assert ListOperations.zipper([1, 2, 3], [2, 5, 3, 7], ["a", "b", "c"], fillvalue=None) == [
            [1, 2, "a"],
            [2, 5, "b"],
            [3, 3, "c"],
            [None, 7, None],
        ]


class TestMiscellaneousOperations:
    @pytest.mark.parametrize(
        "input1, input2, input3, result",
        [
            (list(range(5)), list(range(100)), list(range(50)), list(range(100))),
            (
                "A first string",
                "A second string",
                "One longer than the previous strings",
                "One longer than the previous strings",
            ),
            (list(range(5)), "A somewhat long string", list(range(10)), "A somewhat long string"),
            ([], [], [], []),
            ([], "", "Non empty string", "Non empty string"),
            (list(range(15)), [], "", list(range(15))),
        ],
    )
    def test_longest_item(self, input1, input2, input3, result):
        assert MiscellaneousOperations.longest_item(input1, input2, input3) == result

    def test_longest_item_none_input(self):
        with pytest.raises(TypeError):
            MiscellaneousOperations.longest_item(list(range(5)), None)

    @pytest.mark.parametrize(
        "obj, func, result",
        [
            (
                {"a": 0, "b": 1, "c": 2, "d": 3},
                lambda x: x % 2 == 0,
                {"a": True, "b": False, "c": True, "d": False},
            ),
            (
                {"a": list(range(5)), "b": list(range(10)), "c": list(range(15))},
                lambda x: len(x),
                {"a": 5, "b": 10, "c": 15},
            ),
            (
                {"a": 0.5, "b": 0.9, "c": 1.2, "d": 2.1, "e": 25},
                math.floor,
                {"a": 0, "b": 0, "c": 1, "d": 2, "e": 25},
            ),
        ],
    )
    def test_map_values_to_bool(self, obj, func, result):
        assert MiscellaneousOperations.map_values(obj, func) == result


class TestMultiProcessorExecutor:
    @pytest.mark.parametrize(
        "function, inputs, results",
        [
            (_square, list(range(6)), [0, 1, 4, 9, 16, 25]),
            (_square, [10 * i for i in range(10)], [e ** 2 for e in [10 * i for i in range(10)]]),
            (_to_str, list(range(6)), [str(e) for e in range(6)]),
            (_to_str, [10 * i for i in range(10)], [str(e) for e in [10 * i for i in range(10)]]),
        ],
    )
    @pytest.mark.parametrize("processes", list(range(1, multiprocessing.cpu_count() + 1)))
    def test_multiprocessor(self, function, inputs, results, processes):
        assert (
            MultiProcessor.execute_function(func=function, func_args=inputs, n_processes=processes) == results
        )

    def test_multiprocessing_zero_processes(self):
        with pytest.raises(ValueError):
            MultiProcessor.execute_function(func=_square, func_args=list(range(6)), n_processes=0)


class TestMultiThreaderExecutor:
    @pytest.mark.parametrize(
        "function, inputs, results",
        [
            (_square, list(range(6)), [0, 1, 4, 9, 16, 25]),
            (_square, [10 * i for i in range(10)], [e ** 2 for e in [10 * i for i in range(10)]]),
            (_to_str, list(range(6)), [str(e) for e in range(6)]),
            (_to_str, [10 * i for i in range(10)], [str(e) for e in [10 * i for i in range(10)]]),
        ],
    )
    @pytest.mark.parametrize("threads", list(range(1, 20)))
    def test_multithreading(self, function, inputs, results, threads):
        assert MultiThreader.execute_function(func=function, func_args=inputs, n_threads=threads) == results

    def test_multithreading_zero_threads(self):
        with pytest.raises(ValueError):
            MultiThreader.execute_function(func=_square, func_args=list(range(6)), n_threads=0)


class TestNumberOperations:
    @pytest.mark.parametrize(
        "number, lowthreshold, highthreshold, result",
        [
            (17, 4, 5, 5),
            (50, 70, 100, 70),
            (15, 10, 20, 15),
            (50.5, 50.1, 50.9, 50.5),
            (17.6, 20.1, 44.7, 20.1),
            (-20, -30, 30, -20),
            (3 / 5, 2 / 5, 4 / 5, 3 / 5),
        ],
    )
    def test_clamp_number(self, number, lowthreshold, highthreshold, result):
        assert NumberOperations.clamp_number(number, lowthreshold, highthreshold) == result

    @pytest.mark.parametrize(
        "wrong_input, expected_error",
        [(None, TypeError), (str(5), TypeError), (lambda x: x, TypeError), (object, TypeError)],
    )
    def test_clamp_number_fails(self, wrong_input, expected_error):
        with pytest.raises(expected_error):
            NumberOperations.clamp_number(17, 5, wrong_input)

    @pytest.mark.parametrize(
        "degrees, decompose_bool, result",
        [
            (160, False, 2.792526803190927),
            (160, None, 2.792526803190927),
            (360, True, (2, "pi", "rad")),
            (-360, True, (-2, "pi", "rad")),
            (-1 / 3, False, -0.005817764173314431),
        ],
    )
    def test_degrees_to_radians(self, degrees, decompose_bool, result):
        assert NumberOperations.degrees_to_radians(degrees, decompose_bool) == result

    @pytest.mark.parametrize(
        "inputs, result", [([54, 24], 6), ([30, 132, 378, 582, 738], 6), ([57, 37, 18], 1), ([0, 0], 0)],
    )
    def test_greatest_common_divisor(self, inputs, result):
        assert NumberOperations.greatest_common_divisor(inputs) == result

    @pytest.mark.parametrize("inputs, error", [([50, _square], TypeError)])
    def test_greatest_common_divisor_fails(self, inputs, error):
        with pytest.raises(error):
            NumberOperations.greatest_common_divisor(inputs)

    @pytest.mark.parametrize(
        "number, divisor, result", [(25, 5, True), (73.4, 2.1, False), (-5, 5, True), (-100, -7, False)],
    )
    def test_is_divisible(self, number, divisor, result):
        assert NumberOperations.is_divisible_by(number, divisor) is result

    @pytest.mark.parametrize(
        "number, divisor, error",
        [(50, 0, ZeroDivisionError), (10, _square, TypeError), (str(5), 5, TypeError)],
    )
    def test_is_divisible_fails(self, number, divisor, error):
        with pytest.raises(error):
            NumberOperations.is_divisible_by(number, divisor)

    @pytest.mark.parametrize(
        "args, result", [([4, 5], 20), ([2, 5, 17, 632], 53720), ([-1, 5, 10], -10), ([0, 10, 50], 0)],
    )
    def test_least_common_multiple(self, args, result):
        assert NumberOperations.least_common_multiple(args) == result

    @pytest.mark.parametrize(
        "args, error", [([0, 0], ZeroDivisionError), ([15, _square], TypeError), ([str(100), 10], TypeError)],
    )
    def test_least_common_multiple_fails(self, args, error):
        with pytest.raises(error):
            NumberOperations.least_common_multiple(args)

    @pytest.mark.parametrize(
        "rad, result",
        [
            (2 * math.pi, 360),
            (0.45, 25.783100780887047),
            (2.710, 155.2715624804531),
            (0, 0),
            (-1.5, -85.94366926962348),
        ],
    )
    def test_radians_to_degrees(self, rad, result):
        assert NumberOperations.radians_to_degrees(rad) == result

    @pytest.mark.parametrize("rad, error", [(_square, TypeError), (str(100), TypeError)])
    def test_radians_to_degrees_fails(self, rad, error):
        with pytest.raises(error):
            NumberOperations.radians_to_degrees(rad)


class TestStringOperations:
    @pytest.mark.parametrize(
        "string_input, result",
        [
            ("a_snake_case_name", "aSnakeCaseName"),
            ("A Title Case Name", "aTitleCaseName"),
            ("thatshouldstaythesame", "thatshouldstaythesame"),
        ],
    )
    def test_camel_case(self, string_input, result):
        assert StringOperations.camel_case(string_input) == result

    @pytest.mark.parametrize("string_input, error", [(1, TypeError), ("", IndexError)])
    def test_camel_case_fails(self, string_input, error):
        with pytest.raises(error):
            StringOperations.camel_case(string_input)

    @pytest.mark.parametrize(
        "string_input, lower, result",
        [
            ("astringtocapitalize", False, "Astringtocapitalize"),
            ("astringtocapitalize", None, "Astringtocapitalize"),
            ("astRIngTocApItalizE", True, "Astringtocapitalize"),
            ("", None, ""),
            ("astringtocapitalize", "works_with_anything_not_false", "Astringtocapitalize"),
        ],
    )
    def test_capitalize(self, string_input, lower, result):
        assert StringOperations.capitalize(string_input, lower_rest=lower) == result

    @pytest.mark.parametrize(
        "string_input, lower, error", [(1, True, TypeError), (_square, False, TypeError)]
    )
    def test_camel_case_fails(self, string_input, lower, error):
        with pytest.raises(error):
            StringOperations.capitalize(string_input, lower_rest=lower)

    @pytest.mark.parametrize(
        "string1, string2, result",
        [
            ("Justin Timberlake", "I'm a jerk but listen", True),
            ("I'm a jerk but listen", "Justin Timberlake", True),
            ("Tom Marvolo Riddle", "I am Lord Voldemort", True),
            ("somestring", "Definitely not an anagram", False),
            ("", "", True),
            ("", "mismatched_lengths", False),
        ],
    )
    def test_is_anagram(self, string1, string2, result):
        assert StringOperations.is_anagram(string1, string2) is result

    @pytest.mark.parametrize(
        "string1, string2, error", [(1, "", AttributeError), ("string", False, AttributeError)]
    )
    def test_is_anagram_fails(self, string1, string2, error):
        with pytest.raises(error):
            StringOperations.is_anagram(string1, string2)

    @pytest.mark.parametrize("word, result", [("racecar", True), ("definitelynot", False), ("", True)])
    def test_is_palindrome(self, word, result):
        assert StringOperations.is_palindrome(word) is result

    @pytest.mark.parametrize("word, error", [(1, AttributeError), (_square, AttributeError)])
    def test_is_palindrome_fails(self, word, error):
        with pytest.raises(error):
            StringOperations.is_palindrome(word)

    @pytest.mark.parametrize(
        "string_input, result",
        [
            ("a normal sentence", "a-normal-sentence"),
            ("", ""),
            ("snake_case_string", "snake-case-string"),
            ("thatshouldstaythesame", "thatshouldstaythesame"),
            ("ThatShouldBeLowered", "thatshouldbelowered"),
        ],
    )
    def test_kebab_case(self, string_input, result):
        assert StringOperations.kebab_case(string_input) == result

    @pytest.mark.parametrize("word, error", [(1, TypeError), (_square, TypeError)])
    def test_kebab_case_fails(self, word, error):
        with pytest.raises(error):
            StringOperations.kebab_case(word)

    @pytest.mark.parametrize(
        "string_input, result",
        [
            ("a normal sentence", "a_normal_sentence"),
            ("camelCase", "camelcase"),
            ("", ""),
            ("thatshouldstaythesame", "thatshouldstaythesame"),
            ("ThatShouldBeLowered", "thatshouldbelowered"),
        ],
    )
    def test_snake_case(self, string_input, result):
        assert StringOperations.snake_case(string_input) == result

    @pytest.mark.parametrize("word, error", [(1, TypeError), (_square, TypeError)])
    def test_snake_case_fails(self, word, error):
        with pytest.raises(error):
            StringOperations.snake_case(word)
