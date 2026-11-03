"""pyidh invalid-handle (issue #59), log level (issue #60), failed browse (issue #70), Modbus
source type and browse value_rank checks.

IDH_INVALID_HANDLE used to be a ctypes c_longlong. A ctypes object never compares
equal to the int a handle function returns, so a failed IDHLibrary(), create_source()
or create_group() was never detected.

IDH_LOG_LEVEL used OFF = 255 and had no BIZDT, while ZLOG_LEVEL in libidh.h has
ZLOG_BIZDT = 6 and ZLOG_NONEL = 7, so get_log_level() raised for both.

browse_source() and browse_source_root() built their list from items_count even when the
call failed. A failure that did not write items_count left max_items there, so the caller
got max_items zero-filled entries.

Needs the built library next to pyidh.py: win_amd64/libidh.dll, or linux_x86_64/libidh.so or
linux_aarch64/libidh.so, the symlink to libidh.so.1.0.0 that the install step and the
IndustryDataHub checkout provide. Without it every test is skipped; a library that is there
but does not load is reported as an error, not skipped. No OPC server is required. The same
file is carried verbatim as pyidh/tests/test_pyidh.py in IndustryDataHub, so run it from the
directory that holds tests/ (the repository root here, pyidh/ there):

    python tests/test_pyidh.py -v

IDH_RTSOURCE_MODBUS must have the value libidh.h gives it. The check creates a Modbus source with
IDH_RTSOURCE_FLAG_RECONNECT against a local port the test holds closed, which succeeds while no
device answers, so it needs no server.

idh_browse_item_t gained value_rank in what was its tail padding, so the ctypes mirror must keep
size 1040 and put the field at offset 1039, and both browse calls must return it.

The array calls (read_arrays, write_arrays and the group variants) are checked two ways: mocks of
the C functions cover the marshaling and the re-read of entries whose buffer was too small, and real
calls through a Modbus source, which does not support arrays, check the prototypes and the struct
layout against the library without any server. With IDH_TEST_DA_SERVER and IDH_TEST_DA_NUMERIC_TAG
set (Windows, e.g. opc.da://localhost/TaiJi.OPC.PySim.1 and Demo.Float), a scalar tag is also read as
one element and the value written back, through the source and a group.
"""
from ctypes import byref, c_int, c_void_p, sizeof
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import pyidh  # noqa: E402
except OSError as e:  # pyidh loads the library on import: FileNotFoundError, or a failed load
    pyidh = None
    _load_error = e


def setUpModule():
    if pyidh is None:
        if isinstance(_load_error, FileNotFoundError):
            raise unittest.SkipTest(f"libidh is not built: {_load_error}")
        # The library is there but does not load (a missing runtime dependency, the wrong
        # architecture): that is a defect to show, not an environment to skip
        raise _load_error


class InvalidHandleTests(unittest.TestCase):
    def test_sentinel_is_plain_int_minus_one(self):
        self.assertIs(type(pyidh.IDH_INVALID_HANDLE), int)
        self.assertEqual(pyidh.IDH_INVALID_HANDLE, -1)

    def test_failed_instance_create_raises(self):
        with mock.patch.object(pyidh.libidh, "idh_instance_create", return_value=-1), \
                mock.patch.object(pyidh.libidh, "idh_instance_destroy") as destroy:
            with self.assertRaisesRegex(Exception, "Failed to create IDH instance"):
                pyidh.IDHLibrary()
        destroy.assert_not_called()

    def test_destroy_releases_once_then_keeps_sentinel(self):
        idh = pyidh.IDHLibrary()
        handle = idh.handle
        self.assertNotEqual(handle, pyidh.IDH_INVALID_HANDLE)
        real_destroy = pyidh.libidh.idh_instance_destroy
        with mock.patch.object(pyidh.libidh, "idh_instance_destroy", wraps=real_destroy) as destroy:
            idh.destroy()
            self.assertIs(type(idh.handle), int)
            self.assertEqual(idh.handle, -1)
            idh.destroy()
            idh.__del__()  # called directly, so the check does not depend on when GC finalizes idh
        destroy.assert_called_once_with(handle)

    def test_failed_create_source_and_group_match_sentinel(self):
        idh = pyidh.IDHLibrary()
        try:
            # IDH_RTSOURCE_COUNT is not a source type, so creation fails without a server.
            source = idh.create_source(pyidh.IDH_RTSOURCE.IDH_RTSOURCE_COUNT.value,
                                       "opc.tcp://localhost:4840", 1000, 0)
            self.assertEqual(pyidh.IDH_INVALID_HANDLE, source)
            self.assertFalse(idh.is_source_valid(source))
            group = idh.create_group(source, "Group1")
            self.assertEqual(pyidh.IDH_INVALID_HANDLE, group)
        finally:
            idh.destroy()

    def test_failed_group_create_on_valid_source_matches_sentinel(self):
        # Creating a real source needs a server, so a made-up source handle stands in for one
        # and idh_group_create is mocked to fail.
        source = 0x10001
        idh = pyidh.IDHLibrary()
        try:
            with mock.patch.object(pyidh.libidh, "idh_group_create", return_value=-1) as create:
                group = idh.create_group(source, "Group1")
            create.assert_called_once_with(source, b"Group1")
            self.assertEqual(pyidh.IDH_INVALID_HANDLE, group)
        finally:
            idh.destroy()


class LogLevelTests(unittest.TestCase):
    def setUp(self):
        # The logger only exists once an instance has been created; before that no level is kept.
        self.idh = pyidh.IDHLibrary()
        self.addCleanup(self.idh.destroy)
        saved = c_int()
        self.assertEqual(pyidh.libidh.idh_get_log_level(byref(saved)), 0)
        self.addCleanup(pyidh.libidh.idh_set_log_level, saved.value)

    def test_values_match_zlog_level(self):
        self.assertEqual(pyidh.IDH_LOG_LEVEL.IDH_LOG_LEVEL_BIZDT.value, 6)
        self.assertEqual(pyidh.IDH_LOG_LEVEL.IDH_LOG_LEVEL_OFF.value, 7)
        # One member for each of ZLOG_TRACE..ZLOG_NONEL.
        self.assertEqual([m.value for m in pyidh.IDH_LOG_LEVEL], list(range(8)))

    def test_get_log_level_reports_bizdt_and_off(self):
        for raw, member in ((6, pyidh.IDH_LOG_LEVEL.IDH_LOG_LEVEL_BIZDT),
                            (7, pyidh.IDH_LOG_LEVEL.IDH_LOG_LEVEL_OFF)):
            with self.subTest(level=raw):
                self.assertEqual(pyidh.libidh.idh_set_log_level(raw), 0)
                self.assertIs(self.idh.get_log_level(), member)

    def test_every_member_round_trips(self):
        for member in pyidh.IDH_LOG_LEVEL:
            with self.subTest(member=member.name):
                self.assertEqual(self.idh.set_log_level(member), 0)
                self.assertIs(self.idh.get_log_level(), member)

    def test_out_of_range_level_is_rejected(self):
        warn = pyidh.IDH_LOG_LEVEL.IDH_LOG_LEVEL_WARN
        self.assertEqual(self.idh.set_log_level(warn), 0)
        # set_log_level only takes IDH_LOG_LEVEL members, so call the C function directly.
        # A C++ test cannot pass these without undefined behaviour; see gtest/test_libidh_unit.cpp.
        # ctypes wraps a Python int to c_int's 32 bits, so INT_MAX and INT_MIN are the extremes.
        for raw in (8, 100, 255, -1, 2**31 - 1, -2**31):
            with self.subTest(level=raw):
                self.assertEqual(pyidh.libidh.idh_set_log_level(raw),
                                 pyidh.IDH_ERRCODE.IDH_ERROR_INVALID.value)
                self.assertIs(self.idh.get_log_level(), warn)
        # The last valid level, ZLOG_NONEL, is still accepted.
        self.assertEqual(pyidh.libidh.idh_set_log_level(7), 0)
        self.assertIs(self.idh.get_log_level(), pyidh.IDH_LOG_LEVEL.IDH_LOG_LEVEL_OFF)


class BrowseErrorTests(unittest.TestCase):
    def setUp(self):
        self.idh = pyidh.IDHLibrary()
        self.addCleanup(self.idh.destroy)

    def test_invalid_handle_returns_no_items(self):
        invalid = pyidh.IDH_ERRCODE.IDH_ERRCODE_INVALIDHANDLE.value
        # An unused slot, the sentinel, and the instance handle, which is not a source.
        for source in (123456, pyidh.IDH_INVALID_HANDLE, self.idh.handle):
            with self.subTest(source=source):
                self.assertEqual(self.idh.browse_source_root(source, 10), (invalid, []))
                self.assertEqual(self.idh.browse_source(source, 10, 0, None), (invalid, []))

    def test_failure_that_leaves_items_count_returns_no_items(self):
        # libidh now sets items_count to 0 on every failure, so this case cannot be reached
        # through the C API. The mocks fail without writing items_count, which still holds
        # max_items: pyidh itself must not read it after a failure. NOVALUE (no children) is
        # the most common one.
        source = 0x10001
        for code in (pyidh.IDH_ERRCODE.IDH_ERRCODE_NOVALUE, pyidh.IDH_ERRCODE.IDH_ERRCODE_INVALIDSERVER,
                     pyidh.IDH_ERRCODE.IDH_ERROR_TIMEOUT):
            with self.subTest(code=code.name), \
                    mock.patch.object(pyidh.libidh, "idh_source_browse_root", return_value=code.value), \
                    mock.patch.object(pyidh.libidh, "idh_source_browse", return_value=code.value):
                self.assertEqual(self.idh.browse_source_root(source, 10), (code.value, []))
                self.assertEqual(self.idh.browse_source(source, 10, 0, "Demo"), (code.value, []))


class BrowseValueRankTests(unittest.TestCase):
    """idh_browse_item_t.value_rank sits in the struct's old tail padding (libidh.h)."""

    def test_value_rank_uses_the_old_tail_padding(self):
        self.assertEqual(1040, sizeof(pyidh.idh_browse_item_t))
        self.assertEqual(1038, pyidh.idh_browse_item_t.has_children.offset)
        self.assertEqual(1039, pyidh.idh_browse_item_t.value_rank.offset)

    def test_value_rank_is_signed(self):
        item = pyidh.idh_browse_item_t()
        item.value_rank = pyidh.IDH_VALUERANK_SCALAR_OR_ONE_DIMENSION
        self.assertEqual(-3, item.value_rank)

    def test_browse_results_carry_value_rank(self):
        ranks = (pyidh.IDH_VALUERANK_SCALAR, pyidh.IDH_VALUERANK_ONE_DIMENSION, 2)

        def fill(items, count_ref):
            for i, rank in enumerate(ranks):
                items[i].value_rank = rank
            count_ref._obj.value = len(ranks)
            return len(ranks)

        idh = pyidh.IDHLibrary()
        self.addCleanup(idh.destroy)
        source = 0x10001
        with mock.patch.object(pyidh.libidh, "idh_source_browse",
                               side_effect=lambda s, items, count, ns, name: fill(items, count)), \
                mock.patch.object(pyidh.libidh, "idh_source_browse_root",
                                  side_effect=lambda s, items, count: fill(items, count)):
            for ret, items in (idh.browse_source(source, 10, 0, "Demo"),
                               idh.browse_source_root(source, 10)):
                self.assertEqual(len(ranks), ret)
                self.assertEqual(list(ranks), [item['value_rank'] for item in items])


class ModbusSourceTypeTests(unittest.TestCase):
    def test_values_match_libidh_h(self):
        self.assertEqual(3, pyidh.IDH_RTSOURCE.IDH_RTSOURCE_MODBUS.value)
        self.assertEqual(4, pyidh.IDH_RTSOURCE.IDH_RTSOURCE_COUNT.value)

    def test_modbus_source_type_selects_the_modbus_source(self):
        # The test holds a local port bound but not listening: connects to it are refused, and
        # nothing else can start listening on it while the test runs.
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 0))
        port = blocker.getsockname()[1]
        idh = pyidh.IDHLibrary()
        try:
            modbus = pyidh.IDH_RTSOURCE.IDH_RTSOURCE_MODBUS.value
            reconnect = pyidh.IDH_RTSOURCE_FLAG.IDH_RTSOURCE_FLAG_RECONNECT.value
            # With the reconnect flag a Modbus source is created while no device answers, and keeps
            # reconnecting in the background; it reports itself not valid.
            source = idh.create_source(modbus, f"modbus.tcp://127.0.0.1:{port}?connect_timeout=200",
                                       0, reconnect)
            self.assertNotEqual(pyidh.IDH_INVALID_HANDLE, source)
            self.assertFalse(idh.is_source_valid(source))
            idh.destroy_source(source)
            # Only the Modbus source parses this scheme, and it rejects a string without a host.
            self.assertEqual(pyidh.IDH_INVALID_HANDLE,
                             idh.create_source(modbus, "modbus.tcp://", 0, reconnect))
        finally:
            idh.destroy()
            blocker.close()


if pyidh is not None:  # otherwise setUpModule skips every test
    SHRTLEN = pyidh.IDH_ERRCODE.IDH_ERROR_SHRTLEN.value
    UNSUPPORT = pyidh.IDH_ERRCODE.IDH_ERROR_UNSUPPORT.value
    INVALIDHANDLE = pyidh.IDH_ERRCODE.IDH_ERRCODE_INVALIDHANDLE.value
    FAILED = pyidh.IDH_ERRCODE.IDH_ERRCODE_FAILED.value


def tag(name):
    return {'data_type': 1, 'namespace_index': 2, 'tag_name': name}


class FakeArrayServer:
    """Answers idh_source_readarrays / idh_group_readarrays the way libidh does: copies the elements
    when the buffer is big enough, otherwise IDH_ERROR_SHRTLEN with the length needed. Records what
    each call asked for."""

    def __init__(self, nodes):
        self.nodes = nodes  # key -> (elements, dimensions)
        self.calls = []

    def answer(self, arrays, keys):
        asked = []
        count = 0
        for k, key in enumerate(keys):
            elements, dimensions = self.nodes[key]
            entry = arrays[k]
            asked.append((key, entry.capacity))
            entry.length = len(elements)
            entry.rank = len(dimensions)
            for d, size in enumerate(dimensions[:pyidh.IDH_ARRAY_MAX_RANK]):
                entry.dimensions[d] = size
            entry.element_type = pyidh.IDH_ELEMTYPE.IDH_ELEMTYPE_FLOAT.value
            entry.time_quality = pyidh.idh_real_t.make_time_quality(0xC0, 1234)
            if entry.capacity < len(elements):
                entry.result = SHRTLEN
                continue
            for j, value in enumerate(elements):
                entry.values[j] = value
            entry.result = 0
            count += 1
        self.calls.append(asked)
        return count

    def source_read(self, source, arrays, tags, ranges, size):
        keys = [(tags[k].tag_name.decode(), ranges[k] if ranges else None) for k in range(size)]
        return self.answer(arrays, keys)

    def group_read(self, group, arrays, handles, size):
        return self.answer(arrays, [handles[k] for k in range(size)])


class ArrayStructTests(unittest.TestCase):
    def test_elemtype_values_match_libidh_h(self):
        self.assertEqual(list(range(12)), [m.value for m in pyidh.IDH_ELEMTYPE])
        self.assertEqual(10, pyidh.IDH_ELEMTYPE.IDH_ELEMTYPE_FLOAT.value)
        self.assertEqual(11, pyidh.IDH_ELEMTYPE.IDH_ELEMTYPE_DOUBLE.value)

    def test_layout_matches_libidh_h(self):
        if sizeof(c_void_p) != 8:
            self.skipTest("libidh.h pins the layout on 64-bit only")
        self.assertEqual(48, sizeof(pyidh.idh_array_t))
        offsets = {'values': 0, 'capacity': 8, 'length': 12, 'time_quality': 16, 'result': 24,
                   'element_type': 28, 'rank': 30, 'reserved': 31, 'dimensions': 32}
        for name, offset in offsets.items():
            with self.subTest(field=name):
                self.assertEqual(offset, getattr(pyidh.idh_array_t, name).offset)
        self.assertEqual(16, sizeof(pyidh.idh_array_value_t))
        self.assertEqual(8, pyidh.idh_array_value_t.length.offset)


class ArrayReadTests(unittest.TestCase):
    def setUp(self):
        self.idh = pyidh.IDHLibrary()
        self.addCleanup(self.idh.destroy)
        self.source = 0x10001

    def read(self, server, tags, **kwargs):
        with mock.patch.object(pyidh.libidh, "idh_source_readarrays",
                               side_effect=server.source_read):
            return self.idh.read_arrays(self.source, tags, **kwargs)

    def test_short_buffer_is_read_again_with_the_reported_length(self):
        server = FakeArrayServer({('Short', None): ([1, 2], [2]),
                                  ('Long', None): (list(range(10)), [10])})
        ret, entries = self.read(server, [tag('Short'), tag('Long')], capacity=4)
        self.assertEqual(2, ret)
        # Only the entry that did not fit is read again, with the length it needs
        self.assertEqual([[(('Short', None), 4), (('Long', None), 4)], [(('Long', None), 10)]],
                         server.calls)
        self.assertEqual([1.0, 2.0], entries[0]['values'])
        self.assertEqual([float(v) for v in range(10)], entries[1]['values'])
        self.assertEqual(0, entries[1]['result'])
        self.assertEqual([10], entries[1]['dimensions'])
        self.assertIs(pyidh.IDH_ELEMTYPE.IDH_ELEMTYPE_FLOAT, entries[1]['element_type'])
        self.assertEqual(0xC0, entries[1]['quality'])
        self.assertEqual(1234, entries[1]['timestamp'])

    def test_capacity_zero_sizes_every_buffer_from_a_first_pass(self):
        server = FakeArrayServer({('A', None): ([5, 6, 7], [3]), ('Empty', None): ([], [0])})
        ret, entries = self.read(server, [tag('A'), tag('Empty')], capacity=0)
        self.assertEqual(2, ret)
        self.assertEqual([[(('A', None), 0), (('Empty', None), 0)], [(('A', None), 3)]],
                         server.calls)
        self.assertEqual([5.0, 6.0, 7.0], entries[0]['values'])
        self.assertEqual([], entries[1]['values'])

    def test_index_ranges_follow_their_entries_into_the_retry(self):
        server = FakeArrayServer({('A', b'0:1'): ([1, 2], [2]),
                                  ('A', None): (list(range(8)), [8])})
        ret, entries = self.read(server, [tag('A'), tag('A')], index_ranges=['0:1', ''],
                                 capacity=2)
        self.assertEqual(2, ret)
        self.assertEqual([(('A', None), 8)], server.calls[1])
        with self.assertRaises(ValueError):
            self.idh.read_arrays(self.source, [tag('A')], index_ranges=['0', '1'])

    def test_array_that_keeps_growing_is_tried_three_times(self):
        server = FakeArrayServer({('A', None): ([1, 2], [2])})

        def growing(source, arrays, tags, ranges, size):
            elements, dimensions = server.nodes[('A', None)]
            server.nodes[('A', None)] = (elements + [0] * 3, [len(elements) + 3])
            return server.source_read(source, arrays, tags, ranges, size)

        with mock.patch.object(pyidh.libidh, "idh_source_readarrays", side_effect=growing):
            ret, entries = self.idh.read_arrays(self.source, [tag('A')], capacity=1)
        self.assertEqual(3, len(server.calls))
        self.assertEqual(0, ret)
        self.assertEqual(SHRTLEN, entries[0]['result'])
        self.assertEqual(11, entries[0]['length'])

    def test_failed_retry_keeps_the_short_entry(self):
        server = FakeArrayServer({('A', None): ([1], [1]), ('B', None): ([1, 2, 3], [3])})
        answers = [server.source_read, lambda *args: INVALIDHANDLE]

        def first_then_fail(*args):
            return answers.pop(0)(*args)

        with mock.patch.object(pyidh.libidh, "idh_source_readarrays", side_effect=first_then_fail):
            ret, entries = self.idh.read_arrays(self.source, [tag('A'), tag('B')], capacity=1)
        self.assertEqual(1, ret)
        self.assertEqual(SHRTLEN, entries[1]['result'])
        self.assertEqual(3, entries[1]['length'])
        self.assertEqual([], entries[1]['values'])

    def test_whole_call_failure_returns_its_code(self):
        # The C call leaves the entries alone, as libidh does for an invalid handle
        with mock.patch.object(pyidh.libidh, "idh_source_readarrays",
                               return_value=INVALIDHANDLE) as read:
            ret, entries = self.idh.read_arrays(self.source, [tag('A')])
        read.assert_called_once()
        self.assertEqual(INVALIDHANDLE, ret)
        self.assertEqual(FAILED, entries[0]['result'])
        self.assertEqual(pyidh.IDH_QUALITY.IDH_LOW_INVALID_NODATA.value, entries[0]['quality'])
        self.assertEqual([], entries[0]['values'])

    def test_numpy_values_keep_the_shape(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy is not installed")
        server = FakeArrayServer({('Matrix', None): ([1, 2, 3, 4, 5, 6], [2, 3]),
                                  ('Vector', None): ([1, 2], [2]), ('Scalar', None): ([7], [])})
        ret, entries = self.read(server, [tag('Matrix'), tag('Vector'), tag('Scalar')],
                                 as_numpy=True)
        self.assertEqual(3, ret)
        self.assertEqual((2, 3), entries[0]['values'].shape)
        self.assertEqual(6.0, entries[0]['values'][1, 2])
        self.assertEqual(numpy.float64, entries[0]['values'].dtype)
        self.assertEqual((2,), entries[1]['values'].shape)
        self.assertEqual((1,), entries[2]['values'].shape)  # a scalar is one element
        self.assertEqual(0, entries[2]['rank'])

    def test_group_read_retries_with_the_short_handles(self):
        server = FakeArrayServer({11: ([1], [1]), 12: (list(range(5)), [5])})
        with mock.patch.object(pyidh.libidh, "idh_group_readarrays", side_effect=server.group_read):
            ret, entries = self.idh.read_group_arrays(0x20001, [11, 12], capacity=2)
        self.assertEqual(2, ret)
        self.assertEqual([[(11, 2), (12, 2)], [(12, 5)]], server.calls)
        self.assertEqual([0.0, 1.0, 2.0, 3.0, 4.0], entries[1]['values'])


class ArrayWriteTests(unittest.TestCase):
    def setUp(self):
        self.idh = pyidh.IDHLibrary()
        self.addCleanup(self.idh.destroy)

    @staticmethod
    def captured(values, size):
        return [[values[k].values[j] for j in range(values[k].length)] if values[k].values
                else None for k in range(size)]

    def test_elements_reach_the_library_as_doubles(self):
        seen = {}

        def write(source, results, values, tags, ranges, size):
            seen['values'] = self.captured(values, size)
            seen['tags'] = [tags[k].tag_name for k in range(size)]
            seen['ranges'] = [ranges[k] for k in range(size)] if ranges else None
            for k in range(size):
                results[k] = 0
            return size

        with mock.patch.object(pyidh.libidh, "idh_source_writearrays", side_effect=write):
            ret, results = self.idh.write_arrays(0x10001, [tag('A'), tag('B'), tag('C')],
                                                 [[1, 2.5], (3,), []], index_ranges=['1:2', None, ''])
        self.assertEqual(3, ret)
        self.assertEqual([0, 0, 0], results)
        self.assertEqual([[1.0, 2.5], [3.0], None], seen['values'])  # empty: NULL, length 0
        self.assertEqual([b'A', b'B', b'C'], seen['tags'])
        self.assertEqual([b'1:2', None, None], seen['ranges'])

    def test_numpy_array_is_flattened_row_major(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("numpy is not installed")
        seen = {}

        def write(source, results, values, tags, ranges, size):
            seen['values'] = self.captured(values, size)
            seen['ranges'] = ranges
            return size

        matrix = numpy.array([[1, 2, 3], [4, 5, 6]], order='F')  # stored column-major
        with mock.patch.object(pyidh.libidh, "idh_source_writearrays", side_effect=write):
            self.idh.write_arrays(0x10001, [tag('M')], [matrix])
        self.assertEqual([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]], seen['values'])
        self.assertIsNone(seen['ranges'])

    def test_group_write_passes_the_handles(self):
        seen = {}

        def write(group, results, values, handles, size):
            seen['handles'] = [handles[k] for k in range(size)]
            seen['values'] = self.captured(values, size)
            results[0] = 0
            results[1] = UNSUPPORT
            return 1

        with mock.patch.object(pyidh.libidh, "idh_group_writearrays", side_effect=write):
            ret, results = self.idh.write_group_arrays(0x20001, [11, 12], [[1], [2, 3]])
        self.assertEqual(1, ret)
        self.assertEqual([0, UNSUPPORT], results)
        self.assertEqual([11, 12], seen['handles'])
        self.assertEqual([[1.0], [2.0, 3.0]], seen['values'])

    def test_one_array_per_tag(self):
        with self.assertRaises(ValueError):
            self.idh.write_arrays(0x10001, [tag('A')], [[1], [2]])
        with self.assertRaises(ValueError):
            self.idh.write_group_arrays(0x20001, [11, 12], [[1]])


class ArrayLibraryCallTests(unittest.TestCase):
    """Real calls into libidh. A Modbus source does not support arrays, so it answers every array
    call with IDH_ERROR_UNSUPPORT after checking the arguments and resetting each entry."""

    def setUp(self):
        self.blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.blocker.bind(("127.0.0.1", 0))
        self.addCleanup(self.blocker.close)
        port = self.blocker.getsockname()[1]
        self.idh = pyidh.IDHLibrary()
        self.addCleanup(self.idh.destroy)
        self.source = self.idh.create_source(
            pyidh.IDH_RTSOURCE.IDH_RTSOURCE_MODBUS.value,
            f"modbus.tcp://127.0.0.1:{port}?connect_timeout=200", 0,
            pyidh.IDH_RTSOURCE_FLAG.IDH_RTSOURCE_FLAG_RECONNECT.value)
        self.assertNotEqual(pyidh.IDH_INVALID_HANDLE, self.source)
        self.addCleanup(self.idh.destroy_source, self.source)
        self.tags = [{'data_type': 1, 'namespace_index': 1, 'tag_name': 'hr0'}]

    def assert_reset(self, entry):
        # What libidh writes into each entry before it calls the source
        self.assertEqual(FAILED, entry['result'])
        self.assertEqual(0, entry['length'])
        self.assertEqual(pyidh.IDH_QUALITY.IDH_LOW_INVALID_NODATA.value, entry['quality'])

    def test_source_calls(self):
        ret, entries = self.idh.read_arrays(self.source, self.tags, index_ranges=['0'])
        self.assertEqual(UNSUPPORT, ret)
        self.assert_reset(entries[0])
        self.assertEqual((UNSUPPORT, [FAILED]),
                         self.idh.write_arrays(self.source, self.tags, [[1.0]]))

    def test_group_calls(self):
        group = self.idh.create_group(self.source, "Arrays")
        self.assertNotEqual(pyidh.IDH_INVALID_HANDLE, group)
        self.addCleanup(self.idh.destroy_group, group)
        ret, handles = self.idh.subscribe_group(group, self.tags)
        self.assertEqual(1, ret)
        ret, entries = self.idh.read_group_arrays(group, handles)
        self.assertEqual(UNSUPPORT, ret)
        self.assert_reset(entries[0])
        self.assertEqual((UNSUPPORT, [FAILED]),
                         self.idh.write_group_arrays(group, handles, [[1.0]]))

    def test_invalid_handles(self):
        # libidh returns before it resets the entries, so they must not come back as successes
        # (#94 review)
        for ret, entries in (self.idh.read_arrays(123456, self.tags),
                             self.idh.read_group_arrays(123456, [1])):
            self.assertEqual(INVALIDHANDLE, ret)
            self.assert_reset(entries[0])
            self.assertEqual([], entries[0]['values'])
        self.assertEqual((INVALIDHANDLE, [FAILED]),
                         self.idh.write_arrays(123456, self.tags, [[1.0]]))
        self.assertEqual((INVALIDHANDLE, [FAILED]),
                         self.idh.write_group_arrays(123456, [1], [[1.0]]))


@unittest.skipUnless(os.environ.get("IDH_TEST_DA_SERVER") and os.environ.get("IDH_TEST_DA_NUMERIC_TAG"),
                     "IDH_TEST_DA_SERVER and IDH_TEST_DA_NUMERIC_TAG not set")
class ArrayDAServerTests(unittest.TestCase):
    """Opt-in, against a local OPC DA server. The writes put back the value just read."""

    def test_scalar_is_one_element_through_source_and_group(self):
        idh = pyidh.IDHLibrary()
        self.addCleanup(idh.destroy)
        source = idh.create_source(pyidh.IDH_RTSOURCE.IDH_RTSOURCE_DA.value,
                                   os.environ["IDH_TEST_DA_SERVER"], 0, 0)
        self.assertNotEqual(pyidh.IDH_INVALID_HANDLE, source)
        self.addCleanup(idh.destroy_source, source)
        tags = [{'data_type': 1, 'namespace_index': 0,
                 'tag_name': os.environ["IDH_TEST_DA_NUMERIC_TAG"]}]

        # capacity 0: the library answers IDH_ERROR_SHRTLEN with the length, and pyidh reads again
        ret, entries = idh.read_arrays(source, tags, capacity=0)
        self.assertEqual(1, ret)
        entry = entries[0]
        self.assertEqual(0, entry['result'])
        self.assertEqual(0, entry['rank'])
        self.assertEqual(1, entry['length'])
        self.assertEqual(1, len(entry['values']))
        self.assertIsNot(pyidh.IDH_ELEMTYPE.IDH_ELEMTYPE_UNKNOWN, entry['element_type'])
        self.assertEqual((1, [0]), idh.write_arrays(source, tags, [entry['values']]))

        group = idh.create_group(source, "Arrays")
        self.addCleanup(idh.destroy_group, group)
        ret, handles = idh.subscribe_group(group, tags)
        self.assertEqual(1, ret)
        ret, cached = idh.read_group_arrays(group, handles)
        self.assertEqual(1, ret)
        self.assertEqual(entry['element_type'], cached[0]['element_type'])
        self.assertEqual((1, [0]), idh.write_group_arrays(group, handles, [cached[0]['values']]))
        ret, again = idh.read_group_arrays(group, handles)
        self.assertEqual(1, ret)
        self.assertEqual(cached[0]['values'], again[0]['values'])


if __name__ == "__main__":
    unittest.main()
