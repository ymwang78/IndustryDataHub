"""Server-free tests for the array API and the browse value_rank field.

They exercise the ctypes layer against the real libidh (argument marshalling, structure layout,
the error paths that need no data source) and the buffer-sizing logic of pyidh._read_arrays with
a stand-in for the C read. Reads that need a live OPC UA / DA server are in test_ua.py and
test_da.py.
"""
import ctypes
import unittest

from pyidh import (
    IDHLibrary,
    IDH_DATATYPE,
    IDH_ERRCODE,
    IDH_ELEMTYPE,
    IDH_INVALID_HANDLE,
    IDH_ARRAY_MAX_RANK,
    IDH_VALUERANK_SCALAR_OR_ONE_DIMENSION,
    IDH_VALUERANK_ANY,
    IDH_VALUERANK_SCALAR,
    IDH_VALUERANK_ONE_OR_MORE_DIMENSIONS,
    IDH_VALUERANK_ONE_DIMENSION,
    idh_array_t,
    idh_array_value_t,
    idh_browse_item_t,
)
from pyidh.pyidh import _read_arrays, _ARRAY_READ_ATTEMPTS

SUCCESS = IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value
FAILED = IDH_ERRCODE.IDH_ERRCODE_FAILED.value
SHRTLEN = IDH_ERRCODE.IDH_ERROR_SHRTLEN.value
INVALIDHANDLE = IDH_ERRCODE.IDH_ERRCODE_INVALIDHANDLE.value

TAG = {
    "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
    "namespace_index": 3,
    "tag_name": "Demo.Static.Arrays.Double",
}


def library_read(responses, shapes=None, fail_calls=()):
    """A stand-in for idh_source_readarrays that fills the entries the way libidh does: the
    metadata always; no elements when values is NULL (result 0); IDH_ERROR_SHRTLEN when capacity
    is too small; otherwise the elements. responses[i] are the elements of tag i, row-major, and
    shapes[i] its dimensions (one dimension by default). A call whose 1-based number is in
    fail_calls fails as a whole with IDH_ERRCODE_INVALIDHANDLE and touches nothing.
    read.calls records (capacity, values is not NULL) per entry of every call."""
    shapes = shapes or {}

    def read(positions, arrays):
        read.calls.append([(arrays[k].capacity, bool(arrays[k].values))
                           for k in range(len(positions))])
        if len(read.calls) in fail_calls:
            return INVALIDHANDLE
        count = 0
        for k, i in enumerate(positions):
            elements = responses[i]
            shape = shapes.get(i, (len(elements),))
            arrays[k].length = len(elements)
            arrays[k].element_type = IDH_ELEMTYPE.IDH_ELEMTYPE_DOUBLE.value
            arrays[k].rank = len(shape)
            for d, n in enumerate(shape):
                arrays[k].dimensions[d] = n
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


class ReadArraysBufferSizing(unittest.TestCase):
    def test_capacity_zero_passes_null_then_reads_with_the_reported_length(self):
        read = library_read({0: [1.0, 2.0, 3.0], 1: [5.0]})
        count, entries = _read_arrays(read, 2, 0, False)
        # First pass: no buffer, values NULL. Second pass: one buffer of the reported length each
        self.assertEqual(read.calls, [[(0, False), (0, False)], [(3, True), (1, True)]])
        self.assertEqual(count, 2)
        self.assertEqual([e["result"] for e in entries], [SUCCESS, SUCCESS])
        self.assertEqual([e["values"] for e in entries], [[1.0, 2.0, 3.0], [5.0]])
        self.assertEqual([e["length"] for e in entries], [3, 1])
        self.assertEqual(entries[0]["element_type"], IDH_ELEMTYPE.IDH_ELEMTYPE_DOUBLE)
        self.assertEqual(entries[0]["rank"], 1)
        self.assertEqual(entries[0]["dimensions"], [3])

    def test_short_buffer_is_read_again_only_for_the_entries_that_need_it(self):
        read = library_read({0: [1.0, 2.0, 3.0], 1: [9.0]})
        count, entries = _read_arrays(read, 2, 2, False)
        self.assertEqual(read.calls, [[(2, True), (2, True)], [(3, True)]])
        self.assertEqual(count, 2)
        self.assertEqual([e["values"] for e in entries], [[1.0, 2.0, 3.0], [9.0]])

    def test_enough_capacity_reads_in_one_call(self):
        read = library_read({0: [1.0, 2.0, 3.0]})
        count, entries = _read_arrays(read, 1, 8, False)
        self.assertEqual(read.calls, [[(8, True)]])
        self.assertEqual((count, entries[0]["values"]), (1, [1.0, 2.0, 3.0]))

    def test_empty_array_needs_no_second_pass(self):
        read = library_read({0: []})
        count, entries = _read_arrays(read, 1, 0, False)
        self.assertEqual(read.calls, [[(0, False)]])
        self.assertEqual(count, 1)
        self.assertEqual((entries[0]["result"], entries[0]["values"], entries[0]["length"]),
                         (SUCCESS, [], 0))

    def test_whole_call_failure_is_returned_with_failed_entries(self):
        read = library_read({0: [1.0]}, fail_calls={1})
        count, entries = _read_arrays(read, 1, 0, False)
        self.assertEqual(count, INVALIDHANDLE)
        self.assertEqual(len(read.calls), 1)
        self.assertEqual((entries[0]["result"], entries[0]["values"]), (FAILED, []))

    def test_failed_second_pass_keeps_shrtlen(self):
        read = library_read({0: [1.0, 2.0]}, fail_calls={2})
        count, entries = _read_arrays(read, 1, 0, False)
        self.assertEqual(len(read.calls), 2)
        self.assertEqual(count, 0)
        self.assertEqual((entries[0]["result"], entries[0]["values"], entries[0]["length"]),
                         (SHRTLEN, [], 2))

    def test_retries_are_bounded(self):
        def read(positions, arrays):  # the array grows faster than the buffer, forever
            read.calls += 1
            for k in range(len(positions)):
                arrays[k].length = arrays[k].capacity + 1
                arrays[k].result = SUCCESS if not arrays[k].values else SHRTLEN
            return 0
        read.calls = 0
        count, entries = _read_arrays(read, 1, 0, False)
        self.assertEqual(read.calls, _ARRAY_READ_ATTEMPTS)
        self.assertEqual((count, entries[0]["result"]), (0, SHRTLEN))

    def test_numpy_gives_multi_dimensional_arrays_their_shape(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy is not installed")
        read = library_read({0: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}, shapes={0: (2, 3)})
        count, entries = _read_arrays(read, 1, 0, True)
        self.assertEqual(count, 1)
        self.assertEqual(entries[0]["dimensions"], [2, 3])
        self.assertEqual(entries[0]["values"].shape, (2, 3))
        self.assertEqual(entries[0]["values"][1, 2], 6.0)
        self.assertEqual(entries[0]["values"].dtype, numpy.float64)


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


class StructureLayout(unittest.TestCase):
    """The ctypes structures must match include/idh/libidh.h on every platform."""

    def test_idh_array_t_matches_the_c_layout(self):
        self.assertEqual(ctypes.sizeof(idh_array_t), 48)
        offsets = {name: getattr(idh_array_t, name).offset for name, _ in idh_array_t._fields_}
        self.assertEqual(offsets, {
            "values": 0, "capacity": 8, "length": 12, "time_quality": 16, "result": 24,
            "element_type": 28, "rank": 30, "reserved": 31, "dimensions": 32,
        })
        self.assertEqual(IDH_ARRAY_MAX_RANK, 4)
        self.assertEqual(len(idh_array_t().dimensions), IDH_ARRAY_MAX_RANK)
        self.assertFalse(idh_array_t().values)  # a fresh entry carries a NULL buffer

    def test_idh_array_value_t_matches_the_c_layout(self):
        self.assertEqual(ctypes.sizeof(idh_array_value_t), 16)
        self.assertEqual((idh_array_value_t.values.offset, idh_array_value_t.length.offset), (0, 8))

    def test_browse_item_value_rank_sits_in_the_old_tail_padding(self):
        self.assertEqual(ctypes.sizeof(idh_browse_item_t), 1040)
        self.assertEqual(idh_browse_item_t.value_rank.offset, idh_browse_item_t.has_children.offset + 1)
        self.assertEqual(idh_browse_item_t.value_rank.offset, 1039)
        item = idh_browse_item_t()
        for rank in (IDH_VALUERANK_SCALAR_OR_ONE_DIMENSION, IDH_VALUERANK_ANY, IDH_VALUERANK_SCALAR,
                     IDH_VALUERANK_ONE_OR_MORE_DIMENSIONS, IDH_VALUERANK_ONE_DIMENSION):
            item.value_rank = rank  # int8_t in C: the negative OPC UA ValueRank values round-trip
            self.assertEqual(item.value_rank, rank)
        self.assertEqual((IDH_VALUERANK_SCALAR_OR_ONE_DIMENSION, IDH_VALUERANK_ANY, IDH_VALUERANK_SCALAR,
                          IDH_VALUERANK_ONE_OR_MORE_DIMENSIONS, IDH_VALUERANK_ONE_DIMENSION),
                         (-3, -2, -1, 0, 1))


if __name__ == "__main__":
    unittest.main()
