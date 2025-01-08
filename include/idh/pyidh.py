import ctypes
from ctypes import (
    c_int,
    c_uint,
    c_longlong,
    c_ushort,
    c_byte,
    c_char,
    c_char_p,
    c_double,
    c_void_p,
    POINTER,
    Structure,
    byref,
)
from enum import Enum

import os
import sys

def load_libidh():
    if sys.platform.startswith("win"):
        lib_name = "libidh.dll"
        try:
            lib = ctypes.WinDLL(lib_name)
        except OSError:
            lib_path = os.path.join(os.path.dirname(__file__), lib_name)
            lib = ctypes.WinDLL(lib_path)
    elif sys.platform.startswith("linux"):
        lib_name = "libidh.so"
        try:
            lib = ctypes.CDLL(lib_name)
        except OSError:
            lib_path = os.path.join(os.path.dirname(__file__), lib_name)
            lib = ctypes.CDLL(lib_path)
    else:
        raise OSError("Unsupported platform.")
    return lib

libidh = load_libidh()

def to_signed32(n):
    return n - 0x100000000 if n >= 0x80000000 else n

IDH_INVALID_HANDLE = c_longlong(~0)

class IDH_ERRCODE(Enum):
    IDH_ERRCODE_SUCCESS = 0
    IDH_SUCCEED_IDHBASE = 0x1110000
    IDH_SUCCEED_ALREADYEXIST = 0x1110001
    IDH_ERRCODE_FAILED = -1
    
    IDH_ERROR_COMMON = to_signed32(0x81010000)
    IDH_ERROR_MALLOC = to_signed32(0x81010001)
    IDH_ERROR_UNSUPPORT = to_signed32(0x81010002)
    IDH_ERROR_SHRTLEN = to_signed32(0x81010003)
    IDH_ERROR_EXCDLEN = to_signed32(0x81010004)
    IDH_ERROR_CORRUPT = to_signed32(0x81010005)
    IDH_ERROR_SYNTAX = to_signed32(0x81010006)
    IDH_ERROR_ZIP = to_signed32(0x81010007)
    IDH_ERROR_TIMEOUT = to_signed32(0x81010008)
    IDH_ERROR_CONVERTOR = to_signed32(0x81010009)
    IDH_ERROR_CLOSED = to_signed32(0x8101000A)
    IDH_ERROR_TOCLOSE = to_signed32(0x8101000B)
    IDH_ERROR_PREVNULL = to_signed32(0x8101000C)
    IDH_ERROR_OVERFLOW = to_signed32(0x8101000D)
    IDH_ERROR_INVALID = to_signed32(0x8101000E)
    IDH_ERROR_DUPLICATED = to_signed32(0x8101000F)
    IDH_ERROR_UNINIT = to_signed32(0x81010010)
    IDH_ERROR_BADPRC = to_signed32(0x81010011)
    IDH_ERROR_NORESOURCE = to_signed32(0x81010012)
    IDH_ERROR_VERSION = to_signed32(0x81010013)
    
    IDH_ERRCODE_IDHBASE = to_signed32(0x81110000)
    IDH_ERRCODE_INVALIDTAG = to_signed32(0x81110001)
    IDH_ERRCODE_INVALIDHANDLE = to_signed32(0x81110002)
    IDH_ERRCODE_INVALIDSERVER = to_signed32(0x81110003)
    IDH_ERRCODE_ADDITEM = to_signed32(0x81110004)
    IDH_ERRCODE_NOVALUE = to_signed32(0x81110005)
    IDH_ERRCODE_BADQUANLITY = to_signed32(0x81110006)
    IDH_ERRCODE_UNSUPPORTTYPE = to_signed32(0x81110007)
    IDH_ERRCODE_UNSUBSCRIBED = to_signed32(0x81110008)
    IDH_ERRCODE_NOTALLREADABLE = to_signed32(0x81110009)
    IDH_ERRCODE_HASUNSUBSRIBEDITEM = to_signed32(0x8111000A)
    IDH_ERRCODE_SUBSCRIBEFAILED = to_signed32(0x8111000B)
    IDH_ERRCODE_INCONSISTENT = to_signed32(0x8111000C)
    IDH_ERRCODE_BADSROUCE = to_signed32(0x8111000D)

class IDH_DATATYPE(Enum):
    IDH_DATATYPE_UNKNOW = 0
    IDH_DATATYPE_REAL = 1
    IDH_DATATYPE_TIMESTAMP = 2
    IDH_DATATYPE_STRING = 3

class IDH_QUALITY(Enum):
    IDH_HIGH_INVALID = 0x0
    IDH_HIGH_GOOD = 0x0100
    IDH_HIGH_BAD = 0x0200
    IDH_HIGH_UNCERTAIN = 0x0300
    IDH_HIGH_MASK = 0xff00
    IDH_LOW_INVALID_NODATA = 0x01
    IDH_LOW_INVALID_UNREAD = 0x02
    IDH_LOW_INVALID_UNSUBSCRIBE = 0x03
    IDH_LOW_INVALID_TYPE = 0x04
    IDH_LOW_INVALID_HANDLE = 0x05
    IDH_LOW_INVALID_OVERFLOW = 0x06
    IDH_LOW_INVALID_BADVALUE = 0x07
    IDH_LOW_INVALID_BADQUALITY = 0x08

class IDH_RTSOURCE(Enum):
    IDH_RTSOURCE_UA = 0
    IDH_RTSOURCE_DA = 1
    IDH_RTSOURCE_COUNT = 2

class idh_source_desc_t(Structure):
    _fields_ = [
        ("source_type", c_int),
        ("name", c_char * 256),
        ("schema", c_char * 256),
    ]

class idh_tag_t(Structure):
    _fields_ = [
        ("data_type", c_byte),
        ("namespace_index", c_ushort),
        ("tag_name", c_char_p),
    ]

class idh_real_t(Structure):
    _fields_ = [
        ("quality", c_ushort),        # IDH_QUALITY
        ("timestamp", c_longlong),    # million seconds from epoch
        ("value", c_double),
    ]

# Define opaque pointers as c_longlong
idh_handle_t = c_longlong
idh_source_t = c_longlong
idh_group_t = c_longlong

# idh_instance_create
libidh.idh_instance_create.restype = idh_handle_t
libidh.idh_instance_create.argtypes = []

# idh_instance_destroy
libidh.idh_instance_destroy.restype = None
libidh.idh_instance_destroy.argtypes = [idh_handle_t]

# idh_instance_discovery
libidh.idh_instance_discovery.restype = c_int
libidh.idh_instance_discovery.argtypes = [
    idh_handle_t,
    POINTER(idh_source_desc_t),
    c_uint,
    c_char_p,
    c_ushort,
]

# idh_source_create
libidh.idh_source_create.restype = idh_source_t
libidh.idh_source_create.argtypes = [
    idh_handle_t,
    c_uint,
    c_char_p,
    c_int,
    c_int,
]

# idh_source_valid
libidh.idh_source_valid.restype = c_int
libidh.idh_source_valid.argtypes = [idh_source_t]

# idh_source_destroy
libidh.idh_source_destroy.restype = None
libidh.idh_source_destroy.argtypes = [idh_source_t]

# idh_source_readvalues
libidh.idh_source_readvalues.restype = c_int
libidh.idh_source_readvalues.argtypes = [
    idh_source_t,
    POINTER(idh_real_t),
    POINTER(idh_tag_t),
    c_int,
]

# idh_source_writevalues
libidh.idh_source_writevalues.restype = c_int
libidh.idh_source_writevalues.argtypes = [
    idh_source_t,
    POINTER(c_int),
    POINTER(c_double),
    POINTER(idh_tag_t),
    c_int,
]

# idh_group_create
libidh.idh_group_create.restype = idh_group_t
libidh.idh_group_create.argtypes = [idh_source_t, c_char_p]

# idh_group_subscribe
libidh.idh_group_subscribe.restype = c_int
libidh.idh_group_subscribe.argtypes = [
    idh_group_t,
    POINTER(c_longlong),
    POINTER(idh_tag_t),
    c_uint,
]

# idh_group_unsubscribe
libidh.idh_group_unsubscribe.restype = None
libidh.idh_group_unsubscribe.argtypes = [
    idh_group_t,
    POINTER(c_longlong),
    c_uint,
]

# idh_group_readvalues
libidh.idh_group_readvalues.restype = c_int
libidh.idh_group_readvalues.argtypes = [
    idh_group_t,
    POINTER(idh_real_t),
    POINTER(c_longlong),
    c_uint,
]

# idh_group_writevalues
libidh.idh_group_writevalues.restype = c_int
libidh.idh_group_writevalues.argtypes = [
    idh_group_t,
    POINTER(c_int),
    POINTER(c_double),
    POINTER(c_longlong),
    c_uint,
]

# idh_group_destroy
libidh.idh_group_destroy.restype = None
libidh.idh_group_destroy.argtypes = [idh_group_t]

class IDHLibrary:
    def __init__(self):
        self.handle = libidh.idh_instance_create()
        if IDH_INVALID_HANDLE == self.handle:
            raise Exception("Failed to create IDH instance.")

    def destroy(self):
        if IDH_INVALID_HANDLE != self.handle:
            libidh.idh_instance_destroy(self.handle)
            self.handle = IDH_INVALID_HANDLE

    def discovery(self, source_descs, hostname, port):
        source_size = len(source_descs)
        array_type = idh_source_desc_t * source_size
        source_array = array_type(*source_descs)
        result = libidh.idh_instance_discovery(
            self.handle,
            source_array,
            source_size,
            hostname.encode('utf-8'),
            port
        )
        return result

    def create_source(self, source_type, source_schema, sample_timespan_msec, support_subscribe):
        return libidh.idh_source_create(
            self.handle,
            source_type,
            source_schema.encode('utf-8'),
            sample_timespan_msec,
            support_subscribe
        )

    def is_source_valid(self, source):
        return bool(libidh.idh_source_valid(source))

    def destroy_source(self, source):
        libidh.idh_source_destroy(source)

    def read_values(self, source, tags):
        tags_size = len(tags)
        tag_array = (idh_tag_t * tags_size)()
        for i, tag in enumerate(tags):
            tag_array[i].data_type = tag['data_type']
            tag_array[i].namespace_index = tag['namespace_index']
            tag_array[i].tag_name = tag['tag_name'].encode('utf-8')

        values = (idh_real_t * tags_size)()
        result = libidh.idh_source_readvalues(
            source,
            values,
            tag_array,
            tags_size
        )
        return result, values

    def write_values(self, source, tags, values):
        tags_size = len(tags)
        tag_array = (idh_tag_t * tags_size)()
        for i, tag in enumerate(tags):
            tag_array[i].data_type = tag['data_type']
            tag_array[i].namespace_index = tag['namespace_index']
            tag_array[i].tag_name = tag['tag_name'].encode('utf-8')

        values_array = (c_double * tags_size)(*values)
        results = (c_int * tags_size)()
        result = libidh.idh_source_writevalues(
            source,
            results,
            values_array,
            tag_array,
            tags_size
        )
        return result, list(results)

    def create_group(self, source, group_name):
        return libidh.idh_group_create(
            source,
            group_name.encode('utf-8')
        )

    def subscribe_group(self, group, tags):
        tags_size = len(tags)
        tag_array = (idh_tag_t * tags_size)()
        for i, tag in enumerate(tags):
            tag_array[i].data_type = tag['data_type']
            tag_array[i].namespace_index = tag['namespace_index']
            tag_array[i].tag_name = tag['tag_name'].encode('utf-8')

        handles_or_errcode = (c_longlong * tags_size)()
        result = libidh.idh_group_subscribe(
            group,
            handles_or_errcode,
            tag_array,
            tags_size
        )
        return result, list(handles_or_errcode)

    def unsubscribe_group(self, group, handles):
        tags_size = len(handles)
        handles_array = (c_longlong * tags_size)(*handles)
        libidh.idh_group_unsubscribe(
            group,
            handles_array,
            tags_size
        )

    def read_group_values(self, group, handles):
        tags_size = len(handles)
        handles_array = (c_longlong * tags_size)(*handles)
        values = (idh_real_t * tags_size)()
        result = libidh.idh_group_readvalues(
            group,
            values,
            handles_array,
            tags_size
        )
        return result, values

    def write_group_values(self, group, handles, values):
        tags_size = len(handles)
        handles_array = (c_longlong * tags_size)(*handles)
        values_array = (c_double * tags_size)(*values)
        results = (c_int * tags_size)()
        result = libidh.idh_group_writevalues(
            group,
            results,
            values_array,
            handles_array,
            tags_size
        )
        return result, list(results)

    def destroy_group(self, group):
        libidh.idh_group_destroy(group)

    def __del__(self):
        self.destroy()

def main():
    # Initialize the library
    idh = IDHLibrary()

    # Discovery example
    source_descs = [
        idh_source_desc_t(
            source_type=0,
            name=b"",
            schema=b""
        )
        for _ in range(16)
    ]

    discovery_result = idh.discovery(
        source_descs,
        hostname="localhost",
        port=4840
    )
    print(f"Discovery Result: {discovery_result}")
    for source_desc in source_descs[:discovery_result]:
        print(f"Source Type: {source_desc.source_type}, Name: {source_desc.name.decode('utf-8')}, Schema: {source_desc.schema.decode('utf-8')}")

    # Create a source
    source = idh.create_source(
        source_type=IDH_RTSOURCE.IDH_RTSOURCE_UA.value,
        source_schema="opc.tcp://DESKTOP-S7QB5IR:48010",
        sample_timespan_msec=1000,
        support_subscribe=1
    )
    if IDH_INVALID_HANDLE == source:
        print("Failed to create group.")
        return
    if not idh.is_source_valid(source):
        print("Source is not valid.")
        return

    # Read values example
    tags = [
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 3, "tag_name": "Demo.Dynamic.Scalar.Float"},
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 3, "tag_name": "Demo.Dynamic.Scalar.Int32"},
    ]

    read_result, values = idh.read_values(source, tags)
    print(f"Read Result: {read_result}")
    for value in values:
        print(f"Quality: {value.quality}, Timestamp: {value.timestamp}, Value: {value.value}")

    # Write values example
    write_values = [123.456, 789.012]
    write_result, results = idh.write_values(source, tags, write_values)
    print(f"Write Result: {write_result}, Results: {results}")

    # Batch operations example
    group = idh.create_group(source, "Group1")
    if IDH_INVALID_HANDLE == group:
        print("Failed to create group.")
        return
    subscribe_result, handles = idh.subscribe_group(group, tags)
    # hex print handles
    handles_hex = [hex(handle) for handle in handles]
    print(f"Subscribe Result: {subscribe_result}, Handles: {handles_hex}")

    # Read group values
    group_read_result, group_values = idh.read_group_values(group, handles)
    print(f"Group Read Result: {group_read_result}")
    for value in group_values:
        print(f"Group Quality: {value.quality}, Group Timestamp: {value.timestamp}, Group Value: {value.value}")

    # Write group values
    group_write_values = [654.321, 210.987]
    group_write_result, group_write_results = idh.write_group_values(group, handles, group_write_values)
    print(f"Group Write Result: {group_write_result}, Group Write Results: {group_write_results}")

    # Unsubscribe and destroy group
    idh.unsubscribe_group(group, handles)
    idh.destroy_group(group)

    # Destroy source
    idh.destroy_source(source)

    # Cleanup
    idh.destroy()

if __name__ == "__main__":
    main()