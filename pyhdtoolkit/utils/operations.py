"""
Module utils.operations
-----------------------

Created on 2019.11.12
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection classes with utility functions to perform common / convenient operations on the
classic Python structures.
"""

import copy
import itertools
import math
import random
import re

from functools import reduce
from typing import Callable, Dict, List, Sequence, Tuple, Union


class ListOperations:
    """
    A class to group some common / useful operations on lists.
    """

    @staticmethod
    def all_unique(sequence: Sequence) -> bool:
        """
        Returns True if all the values in a flat list are unique, False otherwise.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            True if all elements are unique, False otherwise.
        """
        return len(sequence) == len(set(sequence))

    @staticmethod
    def average_by(sequence: Sequence, function: Callable = lambda x: x) -> float:
        """
        Returns the average of lst after mapping each element to a value using the
        provided function. Use map() to map each element to the value returned by function.
        Use sum() to sum all of the mapped values, divide by len(lst).

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): function to apply to elements of the sequence.

        Returns:
            The average of each element's result through `function`.

        Usage:
            average_by([{'n': 4}, {'n': 2}, {'n': 8}, {'n': 6}], lambda x: x['n']) -> 5.0
        """
        return float(sum(map(function, sequence), 0.0) / len(sequence))

    @staticmethod
    def bifurcate(sequence: Sequence, filters: List[bool]) -> Sequence:
        """
        Splits values into two groups. If an element in filter is True, the corresponding element
        in the collection belongs to the first group; otherwise, it belongs to the second group.
        Use list comprehension and enumerate() to add elements to groups, based on filter.

        Args:
            sequence (Sequence): a sequence of elements.
            filters (List[bool]): a list of booleans.

        Returns:
            A list of two lists, one for each boolean output of the filters

        Usage:
            bifurcate(['beep', 'boop', 'foo', 'bar'], [True, True, False, True])
            -> [['beep', 'boop', 'bar'], ['foo']]
        """
        return [
            [x for i, x in enumerate(sequence) if filters[i]],
            [x for i, x in enumerate(sequence) if not filters[i]],
        ]

    @staticmethod
    def bifurcate_by(sequence: Sequence, function: Callable) -> list:
        """
        Splits values into two groups according to a function, which specifies which group an
        element in the input list belongs to. If the function returns True, the element belongs
        to the first group; otherwise it belongs to the second group. Use list comprehension to
        add elements to groups, based on function.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on the elements of lst, that should return a boolean.

        Returns:
            A list of two lists, as groups of elements of lst classified depending on their result
            through function.

        Usage:
            bifurcate_by(list(range(5)), lambda x: x % 2 == 0) -> [[0, 2, 4], [1, 3]]
        """
        return [[x for x in sequence if function(x)], [x for x in sequence if not function(x)]]

    @staticmethod
    def chunk_list(sequence: Sequence, size: int) -> Sequence:
        """
        Chunks a list into smaller lists of a specified size. If the size is bigger than initial
        list, return the initial list to avoid unnecessary nesting.
        Use list() and range() to create a list of the desired size. Use map() on the list and
        fill it with splices of the given list. Finally, return use created list.

        Args:
            sequence (Sequence): a sequence of elements.
            size (int): the size of the wanted sublists.

        Returns:
            A list of lists of length `size` (except maybe the last element), with elements
            from `lst`.

        Usage:
            chunk_list(list(range(10)), 3) -> [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        """
        if size > len(sequence):
            return sequence
        return list(
            map(lambda x: sequence[x * size : x * size + size], list(range(math.ceil(len(sequence) / size))),)
        )

    @staticmethod
    def deep_flatten(sequence: Sequence) -> list:
        """
        Deep flattens a list, no matter the nesting levels. This is a recursive approach.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A list with all elements of `lst`, but flattened.

        Usage:
            deep_flatten([["a", "b"], [1, 2], None, [True, False]])
            -> ["a", "b", 1, 2, None True, False]
        """
        return (
            [elem for sublist in sequence for elem in ListOperations.deep_flatten(sublist)]
            if isinstance(sequence, list)
            else [sequence]
        )

    @staticmethod
    def eval_none(sequence: Sequence, function: Callable = lambda x: not not x) -> bool:
        """
        Returns False if the provided function returns True for at least one element in the list,
        True otherwise. Iterate over the elements of the list to test if every element in the
        list returns False based on function. Omit the seconds argument, function, to check if
        all elements are False.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on elements of `sequence` that should return a boolean.

        Returns:
            A boolean. See first line of docstring.

        Usage:
            eval_none([0, 0, 1, 0], lambda x: x >= 2) -> True
            eval_none([0, 1, 2, 0], lambda x: x >= 2) -> False
        """
        return not any(map(function, sequence))

    @staticmethod
    def eval_some(sequence: Sequence, function: Callable = lambda x: not not x) -> bool:
        """
        Returns True if the provided function returns True for at least one element in the list,
        False otherwise. Iterate over the elements of the list to test if every element in the
        list returns True based on function. Omit the seconds argument, function, to check if all
        elements are True.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on elements of `sequence` that should return a boolean.

        Returns:
            A boolean. See first line of docstring.

        Usage:
            eval_some([0, 1, 2, 0], lambda x: x >= 2) -> True
            eval_some([0, 0, 1, 0], lambda x: x >= 2) -> False
        """
        return any(map(function, sequence))

    @staticmethod
    def get_indices(element, sequence: Sequence) -> List[int]:
        """
        Return all array indices at which number is located.

        Args:
            element: any reference element to check.
            sequence (Sequence): a sequence containing objects comparable to `elements`. A string
                can be compared to an int in Python, custom objects probably won't be comparable.

        Returns:
            A list of all indices at which `element` is found in `sequence`. Empty list if
            `element` is not present in `sequence` at all.

        Usage:
            get_indices(0, [0, 1, 3, 5, 7, 3, 9, 0, 0, 5, 3, 2]) -> [0, 7, 8]
        """
        return [i for (y, i) in zip(sequence, range(len(sequence))) if element == y]

    @staticmethod
    def group_by(sequence: Sequence, function: Callable) -> Dict[str, list]:
        """
        Groups the elements of a list based on the given function.
        Use list() in combination with map() and function to map the values of the list to the
        keys of an object. Use list comprehension to map each element to the appropriate key.

        Args:
            sequence (Sequence): a sequence of elements.
            function (Callable): a callable on the elements of `sequence` that should return a
                boolean.

        Returns:
            A dict with keys "True" and "False", each having as value a list of all elements of
            `lst` that were evaluated to respectively `True` or `False` through `function`.

        Usage:
            group_by(list(range(5)), lambda x: x % 2 == 0) -> {True: [0, 2, 4], False: [1, 3]}
        """
        groups = {}
        for key in list(map(function, sequence)):
            groups[key] = [item for item in sequence if function(item) == key]
        return groups

    @staticmethod
    def has_duplicates(sequence: Sequence) -> bool:
        """
        Returns True if there are duplicate values in a fast list, False otherwise.
        Use set() on the given list to remove duplicates, then compare its length with the length
        of the list.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A boolean indicating the presence of duplicates in `lst`.

        Usage:
            has_duplicates([1, 2, 1]) -> True
        """
        return len(sequence) != len(set(sequence))

    @staticmethod
    def sample(sequence: Sequence) -> list:
        """
        Returns a random element from an array.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            A random element from `lst` in a list (to manage potentially nested lists as input).
        """
        return sequence[random.randint(0, len(sequence) - 1)]

    @staticmethod
    def sanitize_list(sequence: Sequence) -> list:
        """
        Removes falsey values from a list. Use filter() to filter out falsey values
        (False, None, 0, and "").

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            The sequence without falsy values.

        Usage:
            sanitize_list([1, False, "a", 2, "", None, 6, 0]) -> [1, "a", 2, 6]
        """
        return list(filter(bool, sequence))

    @staticmethod
    def shuffle(sequence: Sequence) -> Sequence:
        """
        Randomizes the order of the values of an list, returning a new list. Uses an improved
        version of the Fisher-Yates algorithm
        (https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle) to reorder the elements.

        Args:
            sequence (Sequence): a sequence of elements.

        Returns:
            The `lst` with original elements at a random index.
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
        Flattens a list, by spreading its elements into a new list.
        Loop over elements, use list.extend() if the element is a list, list.append() otherwise.
        This might look like deep_flatten but is a subset of its functionality, and is used in
        deep_flatten. This only works if all elements in `lst` are iterables!

        Args:
            sequence (Sequence):  a sequence of elements.

        Returns:
            The sequence flattened, see first docstring sentence.

        Usage:
            spread([list(range(5)), list(range(5))]) -> [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        """
        return list(itertools.chain.from_iterable(sequence))

    @staticmethod
    def symmetric_difference_by(lst_1: Sequence, lst_2: Sequence, function: Callable) -> list:
        """
        Returns the symmetric difference (https://en.wikipedia.org/wiki/Symmetric_difference) of
        lists, after applying the provided function to each list element of both. Create a set by
        applying the function to each element in every list, then use list comprehension in
        combination with function on each one to only keep values not contained in the previously
        created set of the other.

        Args:
            lst_1 (Sequence): a sequence of elements.
            lst_2 (Sequence): a sequence of elements.
            function (Callable): a callable on elements of `lst_1` and `lst_2`.

        Returns:
            A list, see first docstring sentence reference.

        Usage:
            symmetric_difference_by([2.1, 1.2], [2.3, 3.4], math.floor) -> [1.2, 3.4]
            symmetric_difference_by([2.1, 1.2], [0.5, 1.2], lambda x: x >= 2) -> [2.1]
        """
        _lst_1, _lst_2 = set(map(function, lst_1)), set(map(function, lst_2))

        return [item for item in lst_1 if function(item) not in _lst_2] + [
            item for item in lst_2 if function(item) not in _lst_1
        ]

    @staticmethod
    def union_by(lst_1: Sequence, lst_2: Sequence, function: Callable) -> list:
        """
        Returns every element that exists in any of the two lists once, after applying the provided
        function to each element of both. This is the set theory union
        (https://en.wikipedia.org/wiki/Union_(set_theory)) of the two lists, but based on the
        results of applying the function to each list. Python's set() is strange in how is gives
        output, so this function sorts the final list before returning it, in order to give it
        predictable behavior. Create a set by applying the function to each element in lst_1,
        then use list comprehension in combination with function on lst_2 to only keep values not
        contained in the previously created set, _lst_1. Finally, create a set from the previous
        result and _lst_1 and transform it into a list.

        Args:
            lst_1 (Sequence): a sequence of elements.
            lst_2 (Sequence): a sequence of elements.
            function (Callable): a callable on elements of `lst_1` and `lst_2`.

        Returns:
            A list, see first docstring sentence reference.

        Usage:
            union_by([2.1], [1.2, 2.3], math.floor) -> [1.2, 2.1]
        """
        _lst_1 = set(map(function, lst_1))
        return sorted(list(set(lst_1 + [item for item in lst_2 if function(item) not in _lst_1])))

    @staticmethod
    def zipper(*args, fillvalue=None) -> list:
        """
        Creates a list of lists of elements, each internal list being a grouping based on the
        position of elements in the original lists. Essentially, a list containing: a first list
        with all first elements, then a second list with all second elements, etc. Use max
        combined with list comprehension to get the length of the longest list in the arguments.
        Loop for max_length times grouping elements. If lengths of lists vary, use fill_value
        (defaults to None).

        Args:
            *args: a number (>= 2) of different iterables.
            fillvalue: value to use in case of length mismatch.

        Returns:
            A list with the proper level of nesting, and original elements zipped.

        Usage:
            zipper([1, 2, 3], [2, 5, 3, 7], ["a", "b", "c"])
            -> [[1, 2, 'a'], [2, 5, 'b'], [3, 3, 'c'], [None, 7, None]]
        """
        max_length = max(len(lst) for lst in args)
        return [
            [args[k][i] if i < len(args[k]) else fillvalue for k in range(len(args))]
            for i in range(max_length)
        ]


class MiscellaneousOperations:
    """
    A class to group some misc. operations that don't pertain to classic structures.
    """

    @staticmethod
    def longest_item(*args):
        """
        Takes any number of iterable objects or objects with a length property and returns the
        longest one. If multiple objects have the same length, the first one will be returned.
        Use max() with len as the key to return the item with the greatest length.

        Args:
            *args: any number (>= 2) of iterables.

        Returns:
            The longest elements of provided iterables.

        Usage:
            longest_item(list(range(5)), list(range(100)), list(range(50))) -> list(range(100))
        """
        return max(args, key=len)

    @staticmethod
    def map_values(obj: dict, function: Callable) -> dict:
        """
        Creates an new dict with the same keys as the provided dict, and values generated by
        running the provided function on the provided dict's values.
        Use dict.keys() to iterate over the object's keys, assigning the values produced by
        function to each key of a new object.

        Args:
            obj: a dictionary.
            function (Callable): a callable on values of `obj`.

        Returns:
            A new dictionary with the results.

        Usage:
            map_values(
                {"a": list(range(5)), "b": list(range(10)), "c": list(range(15))},
                lambda x: len(x)
            ) -> {"a": 5, "b": 10, "c": 15}
        """
        ret = {}
        for key in obj:
            ret[key] = function(obj[key])
        return ret


class NumberOperations:
    """
    A class to group some common / useful operations on numbers.
    """

    @staticmethod
    def clamp_number(
        num: Union[int, float], a_val: Union[int, float], b_val: Union[int, float]
    ) -> Union[int, float]:
        """
        Clamps num within the inclusive range specified by the boundary values a and b. If num
        falls within the range, return num. Otherwise, return the nearest number in the range.

        Args:
            num (Union[int, float]): a number (float  / int)
            a_val (Union[int, float]): a number (float  / int)
            b_val (Union[int, float]): a number (float  / int)

        Returns:
            A number (float  / int), being the nearest to `num` in the range [`a_val`, `b_val`].

        Usage:
            clamp_number(17, 4, 5) -> 5
            clamp_number(23, 20, 30) -> 23
        """
        return max(min(num, max(a_val, b_val)), min(a_val, b_val))

    @staticmethod
    def degrees_to_radians(
        deg_value: Union[int, float], decompose: bool = False
    ) -> Union[Tuple[float, str, str], int, float]:
        """
        Converts an angle from degrees to radians.
        Use math.pi and the degree to radian formula to convert the angle from degrees to radians.

        Args:
            deg_value (Union[int, float]): angle value in degrees.
            decompose (bool): boolean option to return a more verbose result. Defaults to False.

        Returns:
            The angle value in radians.

        Usage:
            degrees_to_radians(160) -> 2.792526803190927
            degrees_to_radians(360, decompose=True) -> (2, "pi", "rad")
        """
        if decompose:
            return deg_value / 180, "pi", "rad"
        return (deg_value * math.pi) / 180.0

    @staticmethod
    def greatest_common_divisor(numbers_list: Sequence) -> Union[int, float]:
        """
        Calculates the greatest common divisor of a list of numbers.
        Use reduce() and math.gcd over the given list.

        Args:
            numbers_list (Sequence): a list of numbers (floats are advised against as this would
            become a very heavy computation).

        Returns:
            The greatest common divisor of all elements in `numbers_list`.

        Usage:
            greatest_common_divisor([54, 24]) ->
            greatest_common_divisor([30, 132, 378, 582, 738]) -> 6
        """
        return reduce(math.gcd, numbers_list)

    @staticmethod
    def is_divisible_by(dividend: Union[int, float], divisor: Union[int, float]) -> bool:
        """
        Checks if the first numeric argument is divisible by the second one.
        Use the modulo operator (%) to check if the remainder is equal to 0.

        Args:
            dividend (Union[int, float]): a number.
            divisor (Union[int, float]): a number.

        Returns:
            A boolean stating if `dividend` can be divided by `divisor`.
        """
        return dividend % divisor == 0

    @staticmethod
    def least_common_multiple(*args) -> int:
        """
        Returns the least common multiple of two or more numbers.
        Define a function, spread, that uses either list.extend() or list.append() on each element
        in a list to flatten it. Use math.gcd() and lcm(x,y) = x * y / gcd(x,y) to determine the
        least common multiple.

        Args:
            *args: any number (>= 2) of numbers (floats are advised against as this would become a
            very heavy computation).

        Returns:
            The least common multiple of all provided numbers.

        Usage:
            least_common_multiple(4, 5) -> 20
            least_common_multiple(2, 5, 17, 632) -> 53720
        """
        numbers = list(ListOperations.spread(list(args)))

        def _lcm(number1, number2):
            """A least common multiple method for two numbers only"""
            return int(number1 * number2 / math.gcd(number1, number2))

        return reduce(lambda x, y: _lcm(x, y), numbers)

    @staticmethod
    def radians_to_degrees(rad_value: Union[int, float]) -> Union[int, float]:
        """
        Converts an angle from radians to degrees.
        Use math.pi and the radian to degree formula to convert the angle from radians to degrees.

        Args:
            rad_value (Union[int, float]): angle value in degrees.

        Returns:
            The angle value in degrees.

        Usage:
            radians_to_degrees(2* math.pi) -> 360
            radians_to_degrees(2.710) -> 155.2715624804531
        """
        return (rad_value * 180.0) / math.pi


class StringOperations:
    """
    A class to group some common / useful operations on strings.
    """

    @staticmethod
    def camel_case(text: str) -> str:
        """
        Converts a string to camelCase.
        Break the string into words and combine them capitalizing the first letter of each word,
        using a regexp, title() and lower.

        Args:
            text (str): a string.

        Returns:
            The same string best adapted to camel_case.

        Usage:
            camel_case("a_snake_case_name") -> "aSnakeCaseName"
            camel_case("A Title Case Name") -> "aTitleCaseName"
        """
        text = re.sub(r"(\s|_|-)+", " ", text).title().replace(" ", "")
        return text[0].lower() + text[1:]

    @staticmethod
    def capitalize(text: str, lower_rest: bool = False) -> str:
        """
        Capitalizes the first letter of a string, eventually lowers the rest of it.
        Capitalize the first letter of the string and then add it with rest of the string.
        Omit the lower_rest parameter to keep the rest of the string intact, or set it to True
        to convert to lowercase.

        Args:
            text (str): a string.
            lower_rest (bool): boolean option to lower all elements starting from the second.

        Returns:
            The `string`, capitalized.

        Usage:
            capitalize("astringtocapitalize") -> "Astringtocapitalize"
            capitalize("astRIngTocApItalizE", lower_rest=True) -> "Astringtocapitalize"
        """
        return text[:1].upper() + (text[1:].lower() if lower_rest else text[1:])

    @staticmethod
    def is_anagram(str_1: str, str_2: str) -> bool:
        """
        Checks if a string is an anagram of another string (case-insensitive, ignores spaces,
        punctuation and special characters). Use str.replace() to remove spaces from both strings.
        Compare the lengths of the two strings, return False if they are not equal. Use sorted()
        on both strings and compare the results.

        Args:
            str_1 (str): a string.
            str_2 (str): a string.

        Returns:
            A boolean stating whether `str_1` is an anagram of `str_2` or not.

        Usage:
           is_anagram("Tom Marvolo Riddle", "I am Lord Voldemort") -> True
           is_anagram("A first string", "Definitely not an anagram") -> False
        """
        _str1, _str2 = (
            str_1.replace(" ", "").replace("'", ""),
            str_2.replace(" ", "").replace("'", ""),
        )
        return sorted(_str1.lower()) == sorted(_str2.lower())

    @staticmethod
    def is_palindrome(text: str) -> bool:
        """
        Returns True if the given string is a palindrome, False otherwise.
        Use str.lower() and re.sub() to convert to lowercase and remove non-alphanumeric
        characters from the given string. Then compare the new string with its reverse.

        Args:
            text (str): a string.

        Returns:
            A boolean stating whether `string` is a palindrome or not.

        Usage:
            is_palindrome("racecar") -> True
            is_palindrome("definitelynot") -> False
        """
        s_reverse = re.sub(r"[\W_]", "", text.lower())
        return s_reverse == s_reverse[::-1]

    @staticmethod
    def kebab_case(text: str) -> str:
        """
        Converts a string to kebab-case.
        Break the string into words and combine them adding - as a separator, using a regexp.

        Args:
            text (str): a string.

        Returns:
            The same string best adapted to kebab_case.

        Usage:
            kebab_case("camel Case") -> "camel-case"
            kebab_case("snake_case") -> "snake-case"
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
        Converts a string to snake_case.
        Break the string into words and combine them adding _ as a separator, using a regexp.

        Args:
            text (str): a string.

        Returns:
            The same string best adapted to snake_case.

        Usage:
            snake_case("A bunch of words") -> "a_bunch_of_words"
            snake_case("camelCase") -> "camelcase"
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
