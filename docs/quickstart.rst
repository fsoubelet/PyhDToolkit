.. _quickstart:

Quickstart
==========

Zarr provides classes and functions for working with N-dimensional arrays that
behave like NumPy arrays but whose data is divided into chunks and each chunk is
compressed. If you are already familiar with HDF5 then Zarr arrays provide
similar functionality, but with some additional flexibility.

.. _quickstart_create:

Creating an array
-----------------

Zarr has several functions for creating arrays. For example::

    >>> import zarr
    >>> z = zarr.zeros((10000, 10000), chunks=(1000, 1000), dtype='i4')
    >>> z
    <zarr.core.Array (10000, 10000) int32>

The code above creates a 2-dimensional array of 32-bit integers with 10000 rows
and 10000 columns, divided into chunks where each chunk has 1000 rows and 1000
columns (and so there will be 100 chunks in total).

For a complete list of array creation routines see the :mod:`zarr.creation`
module documentation.

.. _quickstart_array:

Reading and writing data
------------------------

Zarr arrays support a similar interface to NumPy arrays for reading and writing
data. For example, the entire array can be filled with a scalar value::

    >>> z[:] = 42

Regions of the array can also be written to, e.g.::

    >>> import numpy as np
    >>> z[0, :] = np.arange(10000)
    >>> z[:, 0] = np.arange(10000)

The contents of the array can be retrieved by slicing, which will load the
requested region into memory as a NumPy array, e.g.::

    >>> z[0, 0]
    0
    >>> z[-1, -1]
    42
    >>> z[0, :]
    array([   0,    1,    2, ..., 9997, 9998, 9999], dtype=int32)
    >>> z[:, 0]
    array([   0,    1,    2, ..., 9997, 9998, 9999], dtype=int32)
    >>> z[:]
    array([[   0,    1,    2, ..., 9997, 9998, 9999],
           [   1,   42,   42, ...,   42,   42,   42],
           [   2,   42,   42, ...,   42,   42,   42],
           ...,
           [9997,   42,   42, ...,   42,   42,   42],
           [9998,   42,   42, ...,   42,   42,   42],
           [9999,   42,   42, ...,   42,   42,   42]], dtype=int32)

.. _quickstart_persist:

Persistent arrays
-----------------

In the examples above, compressed data for each chunk of the array was stored in
main memory. Zarr arrays can also be stored on a file system, enabling
persistence of data between sessions. For example::

    >>> z1 = zarr.open('data/example.zarr', mode='w', shape=(10000, 10000),
    ...                chunks=(1000, 1000), dtype='i4')

The array above will store its configuration metadata and all compressed chunk
data in a directory called 'data/example.zarr' relative to the current working
directory. The :func:`zarr.convenience.open` function provides a convenient way
to create a new persistent array or continue working with an existing
array. Note that although the function is called "open", there is no need to
close an array: data are automatically flushed to disk, and files are
automatically closed whenever an array is modified.

Persistent arrays support the same interface for reading and writing data,
e.g.::

    >>> z1[:] = 42
    >>> z1[0, :] = np.arange(10000)
    >>> z1[:, 0] = np.arange(10000)

Check that the data have been written and can be read again::

    >>> z2 = zarr.open('data/example.zarr', mode='r')
    >>> np.all(z1[:] == z2[:])
    True

If you are just looking for a fast and convenient way to save NumPy arrays to
disk then load back into memory later, the functions
:func:`zarr.convenience.save` and :func:`zarr.convenience.load` may be
useful. E.g.::

    >>> a = np.arange(10)
    >>> zarr.save('data/example.zarr', a)
    >>> zarr.load('data/example.zarr')
    array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

Please note that there are a number of other options for persistent array
storage, see the section on :ref:`tutorial_storage` below.
