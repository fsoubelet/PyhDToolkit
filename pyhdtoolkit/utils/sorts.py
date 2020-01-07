"""
Created on 2019.12.15
:author: Felix Soubelet (felix.soubelet@cern.ch)

This is a pure Python implementation of different sorting algorithms.
Implementation is taken from https://github.com/TheAlgorithms/Python
"""


def quick_sort(collection) -> list:
    """
    The quick sort algorithm (see: https://en.wikipedia.org/wiki/Quicksort) in pure Python.
    :param collection: some mutable ordered collection with heterogeneous comparable items inside.
    :return: the collection sorted in ascending order, as a list.
    """
    if len(collection) <= 1:
        return collection
    else:
        # Use the last element as the first pivot
        pivot = collection.pop()
        # Put elements greater than pivot in greater list
        # Put elements lesser than pivot in lesser list
        greater, lesser = [], []
        for element in collection:
            if element > pivot:
                greater.append(element)
            else:
                lesser.append(element)
        return quick_sort(lesser) + [pivot] + quick_sort(greater)


if __name__ == "__main__":
    raise NotImplementedError("This module is meant to be imported.")
