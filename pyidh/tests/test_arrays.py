"""Server-free array API checks that test_pyidh.py (the copy of libidh's suite) does not make:

- read_arrays(capacity=0) hands libidh a NULL values pointer on its sizing pass, as the header
  asks for a metadata-only read, instead of a pointer to a zero-length ctypes array;
- read_arrays / write_arrays / read_group_arrays / write_group_arrays reach the real library and
  come back through the ctypes declarations on the invalid-handle path, with the per-entry
  results left as preset.

The sizing and retry logic, numpy shaping and the structure layouts are covered in test_pyidh.py.
"""
import unittest

from pyidh import (
    IDHLibrary,
    IDH_DATATYPE,
    IDH_ERRCODE,
    IDH_ELEMTYPE,
    IDH_INVALID_HANDLE,
)
from pyidh.pyidh import _read_arrays

SUCCESS = IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value
FAILED = IDH_ERRCODE.IDH_ERRCODE_FAILED.value
SHRTLEN = IDH_ERRCODE.IDH_ERROR_SHRTLEN.value
INVALIDHANDLE = IDH_ERRCODE.IDH_ERRCODE_INVALIDHANDLE.value

TAG = {
    "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
    "namespace_index": 3,
    "tag_name": "Demo.Static.Arrays.Double",
}


def library_read(responses):
    """A stand-in for idh_source_readarrays that fills the entries the way libidh does: the
    metadata always; no elements when values is NULL (result 0); IDH_ERROR_SHRTLEN when capacity
    is too small; otherwise the elements. responses[i] are the elements of tag i.
    read.calls records (capacity, values is not NULL) per entry of every call."""
    def read(positions, arrays):
        read.calls.append([(arrays[k].capacity, bool(arrays[k].values))
                           for k in range(len(positions))])
        count = 0
        for k, i in enumerate(positions):
            elements = responses[i]
            arrays[k].length = len(elements)
            arrays[k].element_type = IDH_ELEMTYPE.IDH_ELEMTYPE_DOUBLE.value
            arrays[k].rank = 1
            arrays[k].dimensions[0] = len(elements)
            if not arrays[k].values:
                arrays[k].result = SUCCESS
            elif arrays[k].capacity < len(elements):
                arrays[k].result = SHRTLEN
            else:
                for j, v in enumerate(elements):
                    arrays[k].values[j] = v
                arrays[k].result = SUCCESS
            count += arrays[k].result == SUCCESS
        return count

    read.calls = []
    return read


class SizingPassSendsNull(unittest.TestCase):
    def test_capacity_zero_passes_null_then_reads_with_the_reported_length(self):
        read = library_read({0: [1.0, 2.0, 3.0], 1: [5.0]})
        count, entries = _read_arrays(read, 2, 0, False)
        # First pass: no buffer, values NULL, which libidh answers with result 0 and the length.
        # Second pass: one buffer of the reported length each
        self.assertEqual(read.calls, [[(0, False), (0, False)], [(3, True), (1, True)]])
        self.assertEqual(count, 2)
        self.assertEqual([e["result"] for e in entries], [SUCCESS, SUCCESS])
        self.assertEqual([e["values"] for e in entries], [[1.0, 2.0, 3.0], [5.0]])
        self.assertEqual([e["length"] for e in entries], [3, 1])

    def test_empty_array_needs_no_second_pass(self):
        read = library_read({0: []})
        count, entries = _read_arrays(read, 1, 0, False)
        self.assertEqual(read.calls, [[(0, False)]])
        self.assertEqual(count, 1)
        self.assertEqual((entries[0]["result"], entries[0]["values"], entries[0]["length"]),
                         (SUCCESS, [], 0))

    def test_short_buffer_still_reports_shrtlen(self):
        # A buffer that is present but too small keeps the library's own IDH_ERROR_SHRTLEN path
        read = library_read({0: [1.0, 2.0, 3.0]})
        count, entries = _read_arrays(read, 1, 2, False)
        self.assertEqual(read.calls, [[(2, True)], [(3, True)]])
        self.assertEqual((count, entries[0]["values"]), (1, [1.0, 2.0, 3.0]))


class ArrayApiThroughTheLibrary(unittest.TestCase):
    """The calls reach libidh and come back through the ctypes declarations; without a data
    source every call must fail on the handle, with the per-entry results left as preset."""

    def setUp(self):
        self.idh = IDHLibrary()

    def tearDown(self):
        self.idh.destroy()

    def assertFailedEntry(self, entry):
        self.assertEqual(entry["result"], FAILED)
        self.assertEqual(entry["values"], [])
        self.assertEqual(entry["length"], 0)
        self.assertEqual(entry["element_type"], IDH_ELEMTYPE.IDH_ELEMTYPE_UNKNOWN)
        self.assertEqual(entry["rank"], 0)
        self.assertEqual(entry["dimensions"], [])

    def test_read_arrays_with_an_invalid_source_handle(self):
        for capacity in (0, 4):
            result, entries = self.idh.read_arrays(IDH_INVALID_HANDLE, [TAG, TAG], capacity=capacity)
            self.assertEqual(result, INVALIDHANDLE)
            self.assertEqual(len(entries), 2)
            for entry in entries:
                self.assertFailedEntry(entry)

    def test_read_arrays_passes_index_ranges(self):
        result, entries = self.idh.read_arrays(IDH_INVALID_HANDLE, [TAG, TAG], index_ranges=["0:1", ""])
        self.assertEqual(result, INVALIDHANDLE)
        self.assertEqual(len(entries), 2)
        with self.assertRaises(ValueError):
            self.idh.read_arrays(IDH_INVALID_HANDLE, [TAG, TAG], index_ranges=["0:1"])

    def test_write_arrays_with_an_invalid_source_handle(self):
        result, results = self.idh.write_arrays(IDH_INVALID_HANDLE, [TAG, TAG], [[1.0, 2.0, 3.0], []])
        self.assertEqual(result, INVALIDHANDLE)
        self.assertEqual(results, [FAILED, FAILED])
        with self.assertRaises(ValueError):
            self.idh.write_arrays(IDH_INVALID_HANDLE, [TAG], [[1.0], [2.0]])

    def test_write_arrays_flattens_numpy_arrays(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy is not installed")
        result, results = self.idh.write_arrays(IDH_INVALID_HANDLE, [TAG], [numpy.zeros((2, 3))])
        self.assertEqual((result, results), (INVALIDHANDLE, [FAILED]))

    def test_group_arrays_with_an_invalid_group_handle(self):
        result, entries = self.idh.read_group_arrays(IDH_INVALID_HANDLE, [1, 2], capacity=0)
        self.assertEqual(result, INVALIDHANDLE)
        self.assertEqual(len(entries), 2)
        for entry in entries:
            self.assertFailedEntry(entry)
        result, results = self.idh.write_group_arrays(IDH_INVALID_HANDLE, [1], [[1.0]])
        self.assertEqual((result, results), (INVALIDHANDLE, [FAILED]))
        with self.assertRaises(ValueError):
            self.idh.write_group_arrays(IDH_INVALID_HANDLE, [1, 2], [[1.0]])


if __name__ == "__main__":
    unittest.main()
