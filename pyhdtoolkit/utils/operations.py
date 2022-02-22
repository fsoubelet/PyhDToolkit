"""
.. _utils-operations:

Operations Utilities
--------------------

A collection classes with utility functions to perform common / convenient 
operations on the classic Python structures.

.. warning::
   This module contains un-used code and will be removed in a future release.
"""

import copy
import itertools
import math
import random
import re

from functools import reduce
from typing import Callable, Dict, List, Sequence, Tuple, Union


class ListOperations:
    """A class to group some common / useful operations on lists or sequences."""

    @staticmethod
    def all_unique(sequence: Sequence) -> bool:
        """
        Returns `True` if all the values in a flat list are unique, `False` otherwise.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            `True` if all elements are unique, `False` otherwise.

        Example:
            .. code-block:: python

              >>> ListOperations.all_unique([1, 2, 3, 5, 12, 0])
              True
        """
        return len(sequence) == len(set(sequence))

    @staticmethod
    def average_by(sequence: Sequence, function: Callable = lambda x: x) -> float:
        """
        Returns the average of *sequence* after mapping each element to a value using the
        provided function. Use `map` to map each element to the value returned by *function*.
        Uses `sum` to sum all of the mapped values, divided by `len`.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): function to apply to elements of the sequence.

        Returns:
            The average of each element's result through *function*.

        Example:
            .. code-block:: python

              >>> ListOperations.average_by(
              ...   [{'n': 4}, {'n': 2}, {'n': 8}, {'n': 6}], lambda x: x['n']
              ... )
              5.0
        """
        return float(sum(map(function, sequence), 0.0) / len(sequence))

    @staticmethod
    def bifurcate(sequence: Sequence, filters: List[bool]) -> Sequence:
        """
        Splits values into two groups. If an element in filter is `True`, the corresponding
        element in the collection belongs to the first group; otherwise, it belongs to the
        second group. Uses list comprehension and `enumerate` to add elements to groups,
        based on *filter*.

        Args:
            sequence (Sequence): a sequence of elements.
            filters (List[bool]): a list of booleans.

        Returns:
            A list of two lists, one for each boolean output of the filters.

        Example:
            .. code-block:: python

              >>> ListOperations.bifurcate(['beep', 'boop', 'foo', 'bar'], [True, True, False, True])
              [['beep', 'boop', 'bar'], ['foo']]
        """
        return [
            [x for i, x in enumerate(sequence) if filters[i]],
            [x for i, x in enumerate(sequence) if not filters[i]],
        ]

    @staticmethod
    def bifurcate_by(sequence: Sequence, function: Callable) -> list:
        """
        Splits values into two groups according to a function, which specifies which group an
        element in the input sequence belongs to. If the function returns `True`, the element
        belongs to the first group; otherwise it belongs to the second group. Uses list
        comprehension to add elements to groups, based on *function*.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on the elements of *sequence*, that should return a
                boolean.

        Returns:
            A list of two lists, as groups of elements of *sequence* classified depending on their
            result when passed to *function*.

        Example:
            .. code-block:: python

              >>> ListOperations.bifurcate_by(list(range(5)), lambda x: x % 2 == 0)
              [[0, 2, 4], [1, 3]]
        """
        return [[x for x in sequence if function(x)], [x for x in sequence if not function(x)]]

    @staticmethod
    def chunk_list(sequence: Sequence, size: int) -> Sequence:
        """
        Chunks a sequence into smaller lists of a specified size. If the size is bigger
        than that of *sequence*, return *sequence* to avoid unnecessary nesting. Uses
        `list` and `range` to create a list of the desired size. Uses `map` on that
        list and fills it with splices of *sequence*. Finally, returns the created list.

        Args:
            sequence (Sequence): a sequence of elements.
            size (int): the size of the wanted sublists.

        Returns:
            A `list` of lists of length `size` (except maybe the last element), with
            elements from *sequence*.

        Example:
            .. code-block:: python

              >>> ListOperations.chunk_list(list(range(10)), 3)
              [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        """
        if size > len(sequence):
            return sequence
        return list(map(lambda x: sequence[x * size : x * size + size], list(range(math.ceil(len(sequence) / size)))))

    @staticmethod
    def deep_flatten(sequence: Sequence) -> list:
        """
        Recursively deep flattens *sequence*, no matter the nesting levels.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A `list` with all elements of *sequence*, but flattened.

        Example:
            .. code-block:: python

              >>> ListOperations.deep_flatten([["a", "b"], [1, 2], None, [True, False]])
              ["a", "b", 1, 2, None True, False]
        """
        return (
            [elem for sublist in sequence for elem in ListOperations.deep_flatten(sublist)]
            if isinstance(sequence, list)
            else [sequence]
        )

    @staticmethod
    def eval_none(sequence: Sequence, function: Callable = lambda x: not not x) -> bool:
        """
        Returns `False` if the provided *function* returns `True` for at least one element
        in *sequence*, `True` otherwise. Iterates over *sequence* to test if every element
        returns `False` based on function. Omit the seconds argument, *function*, to check
        if all elements are `False`.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on elements of *sequence* that should return
                a boolean.

        Returns:
            A boolean. See first line of docstring.

        Examples:
            .. code-block:: python

              >>> ListOperations.eval_none([0, 0, 1, 0], lambda x: x >= 2)
              True

            .. code-block:: python

              >>> ListOperations.eval_none([0, 1, 2, 0], lambda x: x >= 2)
              False
        """
        return not any(map(function, sequence))

    @staticmethod
    def eval_some(sequence: Sequence, function: Callable = lambda x: not not x) -> bool:
        """
        Returns `True` if the provided *function* returns `True` for at least one element in
        *sequence*, `False` otherwise. Iterates over the elements of *sequence* to test if every
        element returns `True` based on *function*. Omit the seconds argument, *function*, to check
        if all elements are `True`.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on elements of *sequence* that should return a boolean.

        Returns:
            A boolean. See first line of docstring.

        Examples:
            .. code-block:: python

              >>> ListOperations.eval_some([0, 1, 2, 0], lambda x: x >= 2)
              True

            .. code-block:: python

              >>> ListOperations.eval_some([0, 0, 1, 0], lambda x: x >= 2)
              False
        """
        return any(map(function, sequence))

    @staticmethod
    def get_indices(element, sequence: Sequence) -> List[int]:
        """
        Return all array indices at which *element* is located.

        Args:
            element: any reference element to check.
            sequence (Sequence): a sequence containing objects comparable to *elements*.
                A `string` can be compared to an `int` in Python, custom objects probably
                won't be comparable.

        Returns:
            A `list` of all indices at which *element* is found in *sequence*. Empty list if
            *element* is not present in *sequence* at all.

        Example:
            .. code-block:: python

              >>> ListOperations.get_indices(0, [0, 1, 3, 5, 7, 3, 9, 0, 0, 5, 3, 2])
              [0, 7, 8]
        """
        return [i for (y, i) in zip(sequence, range(len(sequence))) if element == y]

    @staticmethod
    def group_by(sequence: Sequence, function: Callable) -> Dict[str, list]:
        """
        Groups the elements of *sequence* based on the given *function*. Uses `list` in
        combination with `map` and *function* to map the values of *sequence* to the
        keys of an object. Uses list comprehension to map each element to the appropriate key.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on the elements of *sequence* that should return a
                boolean.

        Returns:
            A `dict` with keys `True` and `False`, each having as value a list of all elements of
            *sequence* that were evaluated to respectively `True` or `False` through *function*.

        Example:
            .. code-block:: python

              >>> ListOperations.group_by(list(range(5)), lambda x: x % 2 == 0)
              {True: [0, 2, 4], False: [1, 3]}
        """
        groups = {}
        for key in list(map(function, sequence)):
            groups[key] = [item for item in sequence if function(item) == key]
        return groups

    @staticmethod
    def has_duplicates(sequence: Sequence) -> bool:
        """
        Returns `True` if there are duplicate values in *sequence*, `False` otherwise.
        Uses `set` on the given *sequence* to remove duplicates, then compares its length
        with that of *sequence*.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A boolean indicating the presence of duplicates in *sequence*.

        Example:
            .. code-block:: python

              >>> ListOperations.has_duplicates([1, 2, 1])
              True
        """
        return len(sequence) != len(set(sequence))

    @staticmethod
    def sample(sequence: Sequence) -> list:
        """
        Returns a random element from *sequence*.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A random element from *sequence* in a list (to manage potentially
            nested sequences as input).

        Examples:
            .. code-block:: python

              >>> ListOperations.sample(["a", "b", 1, 2, False])
              2
        """
        return sequence[random.randint(0, len(sequence) - 1)]

    @staticmethod
    def sanitize_list(sequence: Sequence) -> list:
        """
        Removes falsey values from a *sequence*. Uses `filter` to filter out falsey
        values (`False`, `None`, `0`, and `""`).

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            The sequence without falsey values.

        Example:
            .. code-block:: python

              >>> ListOperations.sanitize_list([1, False, "a", 2, "", None, 6, 0])
              [1, "a", 2, 6]
        """
        return list(filter(bool, sequence))

    @staticmethod
    def shuffle(sequence: Sequence) -> Sequence:
        """
        Randomizes the order of the elements in *sequence*, returning a new `list`.
        Uses an improved version of the
        `Fisher-Yates algorithm <https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle>`_
        to reorder the elements.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A copy of *sequence* with original elements at a random index.

        Examples:
            .. code-block:: python

              >>> ListOperations.shuffle(["a", "b", 1, 2, False])
              ['b', 1, False, 2, 'a']
        """
        temp_list = copy.deepcopy(sequence)
        amount_to_shuffle = len(temp_list)
        while amount_to_shuffle > 1:
            rand_index = int(math.floor(random.random() * amount_to_shuffle))
            amount_to_shuffle -= 1
            temp_list[rand_index], temp_list[amount_to_shuffle] = (
                temp_list[amount_to_shuffle],
                temp_list[rand_index],
            )
        return temp_list

    @staticmethod
    def spread(sequence: Sequence) -> list:
        """
        Flattens the provided *sequence*, by spreading its elements into a new `list`.
        Loops over elements, uses `list.extend` if the element is a list, `list.append`
        otherwise. This might look like `~.ListOperations.deep_flatten` but is a subset
        of its functionality, and is used in `~.ListOperations.deep_flatten`.

        .. warning::
            This only works if all elements in *sequence* are iterables.

        Args:
            sequence (Sequence):  a sequence of elements.

        Returns:
            The sequence flattened, see first docstring sentence.

        Example:
            .. code-block:: python

              >>> ListOperations.spread([list(range(5)), list(range(5))])
              [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        """
        return list(itertools.chain.from_iterable(sequence))

    @staticmethod
    def symmetric_difference_by(seq_1: Sequence, seq_2: Sequence, function: Callable) -> list:
        """
        Returns the `symmetric difference <https://en.wikipedia.org/wiki/Symmetric_difference>`_
        of the provided sequences, after applying the provided *function* to each element of both.
        Creates a `set` by applying *function* to each element in each sequence, then uses list
        comprehension in combination with *function* on each one to only keep values not contained
        in the previously created set of the other.

        Args:
            lst_1 (Sequence): a sequence of elements.
            lst_2 (Sequence): a sequence of elements.
            function (Callable): a callable on elements of *seq_1* and *seq_2*.

        Returns:
            A `list`, see first docstring sentence reference.

        Examples:
            .. code-block:: python

              >>> ListOperations.symmetric_difference_by([2.1, 1.2], [2.3, 3.4], math.floor)
              [1.2, 3.4]

            .. code-block:: python

              >>> ListOperations.symmetric_difference_by([2.1, 1.2], [0.5, 1.2], lambda x: x >= 2)
              [2.1]
        """
        _lst_1, _lst_2 = set(map(function, seq_1)), set(map(function, seq_2))

        return [item for item in seq_1 if function(item) not in _lst_2] + [
            item for item in seq_2 if function(item) not in _lst_1
        ]

    @staticmethod
    def union_by(seq_1: Sequence, seq_2: Sequence, function: Callable) -> list:
        """
        Returns every element that exists in any of the two sequences once, after
        applying the provided *function* to each element of both. This is the
        `set theory union <https://en.wikipedia.org/wiki/Union_(set_theory)>`_ of the
        two sequences, but based on the results of applying *function* to each.

        .. note::
            Python's  `set` is strange in how is gives output, so this function sorts the
            final list before returning it, in order to give it predictable behavior.

        Creates a `set` by applying *function* to each element in *seq_1*, then uses list
        comprehension in combination with *function* on *seq_2* to only keep values not
        contained in the previously created set, _lst_1. Finally, create a set from the
        previous result and _lst_1, and transform it into a `list`.

        Args:
            lst_1 (Sequence): a sequence of elements.
            lst_2 (Sequence): a sequence of elements.
            function (Callable): a callable on elements of *seq_1* and *seq_2*.

        Returns:
            A `list`, see first docstring sentence reference.

        Example:
            .. code-block:: python

              >>> ListOperations.union_by([2.1], [1.2, 2.3], math.floor)
              [1.2, 2.1]
        """
        _lst_1 = set(map(function, seq_1))
        return sorted(list(set(seq_1 + [item for item in seq_2 if function(item) not in _lst_1])))

    @staticmethod
    def zipper(*args, fillvalue=None) -> list:
        """
        Creates a `list` of lists of elements, each internal list being a grouping based
        on the position of elements in the original sequences. Essentially, a list containing:

        * a first list with all first elements,
        * then a second list with all second elements, etc.

        Uses `max` combined with list comprehension to get the length of the longest list in
        the arguments. Loops for max_length times grouping elements. If lengths of sequences
        vary, uses *fill_value* to adjust the smaller ones (defaults to `None`).

        Args:
            *args: a number (>= 2) of different iterables.
            fillvalue: value to use in case of length mismatch.

        Returns:
            A `list` with the proper level of nesting, and original elements zipped.

        Example:
            .. code-block:: python

              >>> ListOperations.zipper([1, 2, 3], [2, 5, 3, 7], ["a", "b", "c"])
              [[1, 2, 'a'], [2, 5, 'b'], [3, 3, 'c'], [None, 7, None]]
        """
        max_length = max(len(lst) for lst in args)
        return [[args[k][i] if i < len(args[k]) else fillvalue for k in range(len(args))] for i in range(max_length)]


class MiscellaneousOperations:
    """A class to group some misc. operations that don't pertain to classic structures."""

    @staticmethod
    def longest_item(*args):
        """
        Takes any number of iterable objects, or objects with a length property, and returns the
        longest one. If multiple objects have the same length, the first one will be returned.
        Usess `max` with `len` as the key to return the item with the greatest length.

        Args:
            *args: any number (>= 2) of iterables.

        Returns:
            The longest elements of provided iterables.

        Example:
            .. code-block:: python

              >>> MiscellaneousOperations.longest_item(
              ...     list(range(5)), list(range(100)), list(range(50))
              ... )
              list(range(100))
        """
        return max(args, key=len)

    @staticmethod
    def map_values(obj: dict, function: Callable) -> dict:
        """
        Creates an new `dict` with the same keys as the provided *obj*,
        and values generated by running *function* on the *obj*'s values.
        Uses `dict.keys` to iterate over the object's keys, assigning the
        values produced by *function* to each key of a new object.

        Args:
            obj (dict): a dictionary.
            function (Callable): a callable on values of `obj`.

        Returns:
            A new dictionary with the results.

        Example:
            .. code-block:: python

              >>> MiscellaneousOperations.map_values(
              ...     {"a": list(range(5)), "b": list(range(10)), "c": list(range(15))},
              ...     lambda x: len(x)
              ... )
              {"a": 5, "b": 10, "c": 15}
        """
        ret = {}
        for key in obj:
            ret[key] = function(obj[key])
        return ret


class NumberOperations:
    """A class to group some common / useful operations on numbers."""

    @staticmethod
    def clamp_number(num: Union[int, float], a_val: Union[int, float], b_val: Union[int, float]) -> Union[int, float]:
        """
        Clamps *num* within the inclusive range specified by the boundary values *a_val*
        and *b_val*. If *num* falls within the range, returns *num*. Otherwise, return the
        nearest number in the range.

        Args:
            num (Union[int, float]): a number (float  / int)
            a_val (Union[int, float]): a number (float  / int)
            b_val (Union[int, float]): a number (float  / int)

        Returns:
            A number (float  / int), being the nearest to *num* in the range [*a_val*, *b_val*].

        Examples:
            .. code-block:: python

              >>> NumberOperations.clamp_number(17, 4, 5)
              5

            .. code-block:: python

              >>> NumberOperations.clamp_number(23, 20, 30)
              23
        """
        return max(min(num, max(a_val, b_val)), min(a_val, b_val))

    @staticmethod
    def degrees_to_radians(
        deg_value: Union[int, float], decompose: bool = False
    ) -> Union[Tuple[float, str, str], int, float]:
        """
        Converts an angle from degrees to radians. Uses `math.pi` and the degree
        to radian formula to convert the provided *deg_value*.

        Args:
            deg_value (Union[int, float]): angle value in degrees.
            decompose (bool): boolean option to return a more verbose result. Defaults to `False`.

        Returns:
            The angle value in radians.

        Examples:
            .. code-block:: python

              >>> NumberOperations.degrees_to_radians(160)
              2.792526803190927

            .. code-block:: python

              >>> NumberOperations.degrees_to_radians(360, decompose=True)
              (2, "pi", "rad")
        """
        if decompose:
            return deg_value / 180, "pi", "rad"
        return (deg_value * math.pi) / 180.0

    @staticmethod
    def greatest_common_divisor(sequence: Sequence) -> Union[int, float]:
        """
        Calculates the greatest common divisor of a sequence of numbers.
        Uses `reduce` and `math.gcd` over the given *sequence*.

        Args:
            sequence (Sequence): a sequence of numbers (floats are advised against as this would
                become a very heavy computation).

        Returns:
            The greatest common divisor of all elements in *sequence*.

        Examples:
            .. code-block:: python

              >>> NumberOperations.greatest_common_divisor([54, 24])
              6

            .. code-block:: python

              >>> NumberOperations.greatest_common_divisor([30, 132, 378, 582, 738])
              6
        """
        return reduce(math.gcd, sequence)

    @staticmethod
    def is_divisible_by(dividend: Union[int, float], divisor: Union[int, float]) -> bool:
        """
        Checks if the first numeric argument is divisible by the second one.
        Uses the modulo operator (`%`) to check if the remainder is equal to 0.

        Args:
            dividend (Union[int, float]): a number.
            divisor (Union[int, float]): a number.

        Returns:
            A boolean stating if *dividend* can be divided by *divisor*.

        Examples:
            .. code-block:: python

              >>> NumberOperations.is_divisible_by(35, 15)
              False
        """
        return dividend % divisor == 0

    @staticmethod
    def least_common_multiple(*args) -> int:
        """
        Returns the least common multiple of two or more numbers. Defines a function, spread,
        that uses either `list.extend` or `list.append` on each element of s sequence to flatten
        it. Uses `math.gcd` and lcm(x,y) = (x * y) / gcd(x,y) to determine the least common multiple.

        Args:
            *args: any number (>= 2) of numbers (floats are advised against as this would become a
                very heavy computation).

        Returns:
            The least common multiple of all provided numbers.

        Examples:
            .. code-block:: python

              >>> NumberOperations.least_common_multiple(4, 5)
              20

            .. code-block:: python

              >>> NumberOperations.least_common_multiple(2, 5, 17, 632)
              53720
        """
        numbers = list(ListOperations.spread(list(args)))

        def _lcm(number1, number2):
            """A least common multiple method for two numbers only"""
            return int(number1 * number2 / math.gcd(number1, number2))

        return reduce(lambda x, y: _lcm(x, y), numbers)

    @staticmethod
    def radians_to_degrees(rad_value: Union[int, float]) -> Union[int, float]:
        """
        Converts an angle from radians to degrees. Uses `math.pi` and the radian
        to degree formula to convert the provided *rad_value*.

        Args:
            rad_value (Union[int, float]): angle value in degrees.

        Returns:
            The angle value in degrees.

        Examples:
            .. code-block:: python

              >>> NumberOperations.radians_to_degrees(2* math.pi)
              360

            .. code-block:: python

              >>> NumberOperations.radians_to_degrees(2.710)
              155.2715624804531
        """
        return (rad_value * 180.0) / math.pi


class StringOperations:
    """A class to group some common / useful operations on strings."""

    @staticmethod
    def camel_case(text: str) -> str:
        """
        Converts a `string` to camelCase. Breaks the string into words and combines
        them capitalizing the first letter of each word, using a regexp, `title` and `lower`.

        Args:
            text (str): a string.

        Returns:
            The same `string` best adapted to camelCase.

        Examples:
            .. code-block:: python

              >>> StringOperations.camel_case("a_snake_case_name")
              "aSnakeCaseName"

            .. code-block:: python

              >>> StringOperations.camel_case("A Title Case Name")
              "aTitleCaseName"
        """
        text = re.sub(r"(\s|_|-)+", " ", text).title().replace(" ", "")
        return text[0].lower() + text[1:]

    @staticmethod
    def capitalize(text: str, lower_rest: bool = False) -> str:
        """
        Capitalizes the first letter of a `string`, eventually lowers the rest of it.
        Omit the *lower_rest* parameter to keep the rest of the string intact, or set
        it to `True` to convert to lowercase.

        Args:
            text (str): a string.
            lower_rest (bool): boolean option to lower all elements starting from the second.

        Returns:
            The `string`, capitalized.

        Examples:
            .. code-block:: python

              >>> StringOperations.capitalize("astringtocapitalize")
              "Astringtocapitalize"

            .. code-block:: python

              >>> StringOperations.capitalize("astRIngTocApItalizE", lower_rest=True)
              "Astringtocapitalize"
        """
        return text[:1].upper() + (text[1:].lower() if lower_rest else text[1:])

    @staticmethod
    def is_anagram(str_1: str, str_2: str) -> bool:
        """
        Checks if a `string` is an anagram of another string (case-insensitive,
        ignores spaces, punctuation and special characters). Uses `str.replace`
        to remove spaces from both strings. Compares the lengths of the two strings,
        return `False` if they are not equal. Uses `sorted` on both strings and
        compares the results.

        Args:
            str_1 (str): a string.
            str_2 (str): a string.

        Returns:
            A boolean stating whether `str_1` is an anagram of `str_2` or not.

        Examples:
            .. code-block:: python

              >>> StringOperations.is_anagram("Tom Marvolo Riddle", "I am Lord Voldemort")
              True

            .. code-block:: python

              >>> StringOperations.is_anagram("A first string", "Definitely not an anagram")
              False
        """
        _str1, _str2 = (
            str_1.replace(" ", "").replace("'", ""),
            str_2.replace(" ", "").replace("'", ""),
        )
        return sorted(_str1.lower()) == sorted(_str2.lower())

    @staticmethod
    def is_palindrome(text: str) -> bool:
        """
        Returns `True` if the given string is a palindrome, `False` otherwise.
        Uses `str.lower` and `re.sub` to convert to lowercase and remove non-alphanumeric
        characters from the given string. Then compare the new string with its reverse.

        Args:
            text (str): a string.

        Returns:
            A boolean stating whether *text* is a palindrome or not.

        Examples:
            .. code-block:: python

              >>> StringOperations.is_palindrome("racecar")
              True

            .. code-block:: python

              >>> StringOperations.is_palindrome("definitelynot")
              False
        """
        s_reverse = re.sub(r"[\W_]", "", text.lower())
        return s_reverse == s_reverse[::-1]

    @staticmethod
    def kebab_case(text: str) -> str:
        """
        Converts a string to kebab-case. Breaks the string into words and
        combines them adding `-` as a separator, using a regexp.

        Args:
            text (str): a string.

        Returns:
            The same string best adapted to kebab_case.

        Examples:
            .. code-block:: python

              >>> StringOperations.kebab_case("camel Case")
              "camel-case"

            .. code-block:: python

              >>> StringOperations.kebab_case("snake_case")
              "snake-case"
        """
        return re.sub(
            r"(\s|_|-)+",
            "-",
            re.sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: mo.group(0).lower(),
                text,
            ),
        )

    @staticmethod
    def snake_case(text: str) -> str:
        """
        Converts a string to snake_case. Breaks the string into words and
        combines them adding `_` as a separator, using a regexp.

        Args:
            text (str): a string.

        Returns:
            The same string best adapted to snake_case.

        Examples:
            .. code-block:: python

              >>> StringOperations.snake_case("A bunch of words")
              "a_bunch_of_words"

            .. code-block:: python

              >>> StringOperations.snake_case("camelCase")
              "camelcase"
        """
        return re.sub(
            r"(\s|_|-)+",
            "_",
            re.sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: mo.group(0).lower(),
                text,
            ),
        )
