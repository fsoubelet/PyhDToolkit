"""
Created on 2019.11.12
:author: Felix Soubelet (felix.soubelet@cern.ch)

A collection classes with utility functions to perform common / convenient operations on the classic python structures.
"""

import math
import re
from copy import deepcopy
from functools import reduce
from random import randint


class ListOperations:
    """
    A class to group some common / useful operations on lists.
    """

    @staticmethod
    def all_unique(lst: list) -> bool:
        """
        Returns True if all the values in a flat list are unique, False otherwise.
        Use set() on the given list to remove duplicates, compare its length with that of the list.
        """
        return len(lst) == len(set(lst))

    @staticmethod
    def average_by(lst: list, function=lambda x: x) -> float:
        """
        Returns the average of lst after mapping each element to a value using the provided function.
        Use map() to map each element to the value returned by function.
        Use sum() to sum all of the mapped values, divide by len(lst).
        Example:
            average_by([{'n': 4}, {'n': 2}, {'n': 8}, {'n': 6}], lambda x: x['n']) -> 5.0
        """
        return float(sum(map(function, lst), 0.0) / len(lst))

    @staticmethod
    def bifurcate(lst: list, filters: list) -> list:
        """
        Splits values into two groups.
        If an element in filter is True, the corresponding element in the collection belongs to the first group;
        otherwise, it belongs to the second group.
        Use list comprehension and enumerate() to add elements to groups, based on filter.
        Example:
            bifurcate(['beep', 'boop', 'foo', 'bar'], [True, True, False, True]) -> [['beep', 'boop', 'bar'], ['foo']]
        """
        return [[x for i, x in enumerate(lst) if filters[i]], [x for i, x in enumerate(lst) if not filters[i]]]

    @staticmethod
    def bifurcate_by(lst: list, function) -> list:
        """
        Splits values into two groups according to a function, which specifies which group an element in the input list
        belongs to. If the function returns True, the element belongs to the first group; otherwise it belongs to the
        second group.
        Use list comprehension to add elements to groups, based on function.
        """
        return [[x for x in lst if function(x)], [x for x in lst if not function(x)]]

    @staticmethod
    def chunk_list(lst: list, size) -> list:
        """
        Chunks a list into smaller lists of a specified size.
        Use list() and range() to create a list of the desired size.
        Use map() on the list and fill it with splices of the given list.
        Finally, return use created list.
        """
        return list(map(lambda x: lst[x * size : x * size + size], list(range(0, math.ceil(len(lst) / size)))))

    @staticmethod
    def deep_flatten(lst: list) -> list:
        """
        Deep flattens a list.
        Use recursion. Define a function, spread, that uses either list.extend() or list.append() on each element in a
        list to flatten it. Use list.extend() with an empty list and the spread function to flatten a list. Recursively
        flatten each element that is a list.
        """
        result = []
        result.extend(
            ListOperations.spread(
                list(map(lambda x: ListOperations.deep_flatten(x) if isinstance(x, list) else x, lst))
            )
        )
        return result

    @staticmethod
    def group_by(lst: list, function) -> dict:
        """
        Groups the elements of a list based on the given function.
        Use list() in combination with map() and function to map the values of the list to the keys of an object.
        Use list comprehension to map each element to the appropriate key.
        """
        groups = {}
        for key in list(map(function, lst)):
            groups[key] = [item for item in lst if function(item) == key]
        return groups

    @staticmethod
    def has_duplicates(lst: list) -> bool:
        """
        Returns True if there are duplicate values in a fast list, False otherwise.
        Use set() on the given list to remove duplicates, then compare its length with the length of the list.
        """
        return len(lst) != len(set(lst))

    @staticmethod
    def sample(lst: list) -> list:
        """
        Returns a random element from an array.
        Use randint() to generate a random number that corresponds to an index in the list, return the element at that
        index.
        """
        return lst[randint(0, len(lst) - 1)]

    @staticmethod
    def sanitize_list(lst: list) -> list:
        """
        Removes falsey values from a list.
        Use filter() to filter out falsey values (False, None, 0, and "").
        """
        return list(filter(bool, lst))

    @staticmethod
    def shuffle(lst: list) -> list:
        """
        Randomizes the order of the values of an list, returning a new list.
        Uses the Fisher-Yates algorithm (https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle) to reorder the
        elements of the list.
        """
        temp_list = deepcopy(lst)
        m = len(temp_list)
        while m:
            m -= 1
            temp_list[m], temp_list[(randint(0, m))] = temp_list[(randint(0, m))], temp_list[m]
        return temp_list

    @staticmethod
    def some_eval(lst: list, function=lambda x: not not x) -> bool:
        """
        Returns True if the provided function returns True for at least one element in the list, False otherwise.
        Iterate over the elements of the list to test if every element in the list returns True based on function.
        Omit the seconds argument, function, to check if all elements are True.
        Examples:
            some_eval([0, 1, 2, 0], lambda x: x >= 2 ) # True
            some_eval([0, 0, 1, 0]) # True
        """
        for ele in lst:
            if function(ele):
                return True
        return False

    @staticmethod
    def spread(arg) -> list:
        """
        Flattens a list, by spreading its elements into a new list.
        Loop over elements, use list.extend() if the element is a list, list.append() otherwise.
        """
        ret = []
        for i in arg:
            if isinstance(i, list):
                ret.extend(i)
            else:
                ret.append(i)
        return ret

    @staticmethod
    def symmetric_difference_by(lst_1: list, lst_2: list, function) -> list:
        """
        Returns the symmetric difference between two lists, after applying the provided function to each list element of
        both.
        Create a set by applying the function to each element in every list, then use list comprehension in combination
        with fn on each one to only keep values not contained in the previously created set of the other.
        Example:
            symmetric_difference_by([2.1, 1.2], [2.3, 3.4], floor) # [1.2, 3.4]
        """
        _lst_1, _lst_2 = set(map(function, lst_1)), set(map(function, lst_2))
        return [item for item in lst_1 if function(item) not in _lst_2] + [
            item for item in lst_2 if function(item) not in _lst_1
        ]

    @staticmethod
    def union_by(lst_1: list, lst_2: list, function) -> list:
        """
        Returns every element that exists in any of the two lists once, after applying the provided function to each
        element of both.
        Create a set by applying fn to each element in a, then use list comprehension in combination with fn on b to
        only keep values not contained in the previously created set, _a.
        Finally, create a set from the previous result and a and transform it into a list.
        Example:
            union_by([2.1], [1.2, 2.3], floor) # [2.1, 1.2]
        """
        _lst_1 = set(map(function, lst_1))
        return list(set(lst_1 + [item for item in lst_2 if function(item) not in _lst_1]))

    @staticmethod
    def zipper(*args, fillvalue=None) -> list:
        """
        Creates a list of elements, grouped based on the position in the original lists.
        Use max combined with list comprehension to get the length of the longest list in the arguments.
        Loop for max_length times grouping elements.
        If lengths of lists vary, use fill_value (defaults to None).
        """
        max_length = max([len(lst) for lst in args])
        result = []
        for i in range(max_length):
            result.append([args[k][i] if i < len(args[k]) else fillvalue for k in range(len(args))])
        return result


class MiscellaneousOperations:
    """
    A class to group some misc. operations that don't pertain to classic structures.
    """

    @staticmethod
    def longest_item(*args) -> int:
        """
        Takes any number of iterable objects or objects with a length property and returns the longest one.
        If multiple objects have the same length, the first one will be returned.
        Use max() with len as the key to return the item with the greatest length.
        """
        return max(args, key=len)

    @staticmethod
    def map_values(obj: dict, function) -> dict:
        """
        Creates an new dict with the same keys as the provided dict, and values generated by running the provided
        function on the provided dict's values.
        Use dict.keys() to iterate over the object's keys, assigning the values produced by function to each key of
        a new object.
        """
        ret = {}
        for key in obj.keys():
            ret[key] = function(obj[key])
        return ret


class NumberOperations:
    """
    A class to group some common / useful operations on numbers.
    """

    @staticmethod
    def clamp_number(num, a_val, b_val):
        """
        Clamps num within the inclusive range specified by the boundary values a and b.
        If num falls within the range, return num.
        Otherwise, return the nearest number in the range.
        """
        return max(min(num, max(a_val, b_val)), min(a_val, b_val))

    @staticmethod
    def degrees_to_radians(deg_value: float) -> float:
        """
        Converts an angle from degrees to radians.
        Use math.pi and the degree to radian formula to convert the angle from degrees to radians.
        """
        return (deg_value * math.pi) / 180.0

    @staticmethod
    def greater_common_divisor(numbers_list: list) -> float:
        """
        Calculates the greatest common divisor of a list of numbers.
        Use reduce() and math.gcd over the given list.
        """
        return reduce(math.gcd, numbers_list)

    @staticmethod
    def is_divisible_by(dividend, divisor) -> bool:
        """
        Checks if the first numeric argument is divisible by the second one.
        Use the modulo operator (%) to check if the remainder is equal to 0.
        """
        return dividend % divisor == 0

    @staticmethod
    def least_common_multiple(*args) -> float:
        """
        Returns the least common multiple of two or more numbers.
        Define a function, spread, that uses either list.extend() or list.append() on each element in a list to
        flatten it. Use math.gcd() and lcm(x,y) = x * y / gcd(x,y) to determine the least common multiple.
        """
        numbers = []
        numbers.extend(ListOperations.spread(list(args)))

        def _lcm(number1, number2):
            return int(number1 * number2 / math.gcd(number1, number2))

        return reduce(lambda x, y: _lcm(x, y), numbers)

    @staticmethod
    def radians_to_degrees(rad_value: float) -> float:
        """
        Converts an angle from radians to degrees.
        Use math.pi and the radian to degree formula to convert the angle from radians to degrees.
        """
        return (rad_value * 180.0) / math.pi


class StringOperations:
    """
    A class to group some common / useful operations on strings.
    """

    @staticmethod
    def camel_case(string: str) -> str:
        """
        Converts a string to camelCase.
        Break the string into words and combine them capitalizing the first letter of each word, using a regexp,
        title() and lower.
        """
        string = re.sub(r"(\s|_|-)+", " ", string).title().replace(" ", "")
        return string[0].lower() + string[1:]

    @staticmethod
    def capitalize(string: str, lower_rest: bool = False) -> str:
        """
        Capitalizes the first letter of a string.
        Capitalize the first letter of the string and then add it with rest of the string.
        Omit the lower_rest parameter to keep the rest of the string intact, or set it to True to convert to lowercase.
        """
        return string[:1].upper() + (string[1:].lower() if lower_rest else string[1:])

    @staticmethod
    def eval_none(lst: list, function=lambda x: not not x) -> bool:
        """
        Returns False if the provided function returns True for at least one element in the list, True otherwise.
        Iterate over the elements of the list to test if every element in the list returns False based on function.
        Omit the seconds argument, function, to check if all elements are False.
        """
        for ele in lst:
            if function(ele):
                return False
        return True

    @staticmethod
    def is_anagram(str1: str, str2: str) -> bool:
        """
        Checks if a string is an anagram of another string (case-insensitive, ignores spaces, punctuation and special
        characters).
        Use str.replace() to remove spaces from both strings.
        Compare the lengths of the two strings, return False if they are not equal.
        Use sorted() on both strings and compare the results.
        """
        _str1, _str2 = str1.replace(" ", ""), str2.replace(" ", "")
        return False if len(_str1) != len(str2) else sorted(_str1.lower()) == sorted(_str2.lower())

    @staticmethod
    def is_palindrome(string: str) -> bool:
        """
        Returns True if the given string is a palindrome, False otherwise.
        Use str.lower() and re.sub() to convert to lowercase and remove non-alphanumeric
        characters from the given string. Then compare the new string with its reverse.
        """
        s_reverse = re.sub(r"[\W_]", "", string.lower())
        return s_reverse == s_reverse[::-1]

    @staticmethod
    def kebab_case(string: str) -> str:
        """
        Converts a string to kebab-case.
        Break the string into words and combine them adding - as a separator, using a regexp.
        Example:
            kebab_case('camel Case') gives 'camel-case'
        """
        return re.sub(
            r"(\s|_|-)+",
            "-",
            re.sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: mo.group(0).lower(),
                string,
            ),
        )

    @staticmethod
    def snake_case(string: str) -> str:
        """
        Converts a string to snake_case.
        Break the string into words and combine them adding _-_ as a separator, using a regexp.
        """
        return re.sub(
            r"(\s|_|-)+",
            "-",
            re.sub(
                r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                lambda mo: mo.group(0).lower(),
                string,
            ),
        )

    @staticmethod
    def zip_up(*args, fill_value=None) -> list:
        """
        Creates a list of elements, grouped based on the position in the original lists.
        Use max combined with list comprehension to get the length of the longest list in the arguments.
        Loop for max_length times grouping elements. If lengths of lists vary, use fill_value (defaults to None).
        Examples:
            zip_up(['a', 'b'], [1, 2], [True, False]) # [['a', 1, True], ['b', 2, False]]
            zip_up(['a'], [1, 2], [True, False]) # [['a', 1, True], [None, 2, False]]
            zip_up(['a'], [1, 2], [True, False], fill_value = '_') # [['a', 1, True], ['_', 2, False]]
        """
        max_length = max([len(lst) for lst in args])
        result = []
        for i in range(max_length):
            result.append([args[k][i] if i < len(args[k]) else fill_value for k in range(len(args))])
        return result


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
