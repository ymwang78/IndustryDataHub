import ctypes
from ctypes import (
    c_int,
    c_int32,
    c_uint,
    c_uint8,
    c_uint16,
    c_uint32,
    c_ulonglong,  # for uint64_t
    c_longlong,
    c_ushort,
    c_ubyte,
    c_byte,
    c_char,
    c_char_p,
    c_double,
    c_void_p,
    POINTER,
    Structure,
    byref,
    cast,
)
from enum import Enum
import ctypes.util
import os
import sys
import platform

def load_libidh():
    # 当前包目录
    lib_dir = os.path.dirname(os.path.abspath(__file__))

    # 平台目录名称要和 setup.py 中保持一致
    if sys.platform.startswith("win"):
        arch = "win_amd64" if platform.machine().lower() in ["x86_64", "amd64"] else "win_arm64"
        lib_name = "libidh.dll"
    elif sys.platform.startswith("linux"):
        arch = "linux_x86_64" if platform.machine().lower() in ["x86_64", "amd64"] else "linux_aarch64"
        lib_name = "libidh.so"
    else:
        raise OSError(f"Unsupported platform: {sys.platform}")

    platform_dir = os.path.join(lib_dir, arch)
    lib_path = os.path.join(platform_dir, lib_name)

    if not os.path.exists(lib_path):
        raise FileNotFoundError(f"Could not find {lib_name} in {platform_dir}")

    try:
        if sys.platform.startswith("win"):
            lib = ctypes.WinDLL(lib_path)
        else:
            lib = ctypes.CDLL(lib_path)
        print(f"Loaded {lib_name} from {platform_dir}")
        return lib
    except OSError as e:
        raise OSError(f"Failed to load {lib_name} from {platform_dir}: {e}")

libidh = load_libidh()

def to_signed32(n):
    return n - 0x100000000 if n >= 0x80000000 else n

# Plain int, not c_longlong: handle functions return int, and a ctypes object never equals one.
IDH_INVALID_HANDLE = -1

# 日志级别枚举，取值与 libidh.h 的 ZLOG_LEVEL 一致
class IDH_LOG_LEVEL(Enum):
    IDH_LOG_LEVEL_TRACE = 0    # 最详细的日志级别
    IDH_LOG_LEVEL_DEBUG = 1    # 调试信息
    IDH_LOG_LEVEL_INFO = 2     # 一般信息
    IDH_LOG_LEVEL_WARN = 3     # 警告信息
    IDH_LOG_LEVEL_ERROR = 4    # 错误信息
    IDH_LOG_LEVEL_FATAL = 5    # 致命错误
    IDH_LOG_LEVEL_BIZDT = 6    # 业务数据日志 (ZLOG_BIZDT)
    IDH_LOG_LEVEL_OFF = 7      # 关闭日志 (ZLOG_NONEL)

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

# Browse items' value_rank, the same values as the OPC UA ValueRank attribute. Plain ints, not an
# Enum: a value n > 1 is an array with exactly n dimensions.
IDH_VALUERANK_SCALAR_OR_ONE_DIMENSION = -3
IDH_VALUERANK_ANY = -2  # scalar or array of any rank, or unknown
IDH_VALUERANK_SCALAR = -1
IDH_VALUERANK_ONE_OR_MORE_DIMENSIONS = 0  # array, rank not fixed (OPC DA arrays)
IDH_VALUERANK_ONE_DIMENSION = 1

# Element type of an array value, see idh_array_t.element_type. Elements are always passed as
# double; this says what the server holds, for example to compare a Float array at float precision.
class IDH_ELEMTYPE(Enum):
    IDH_ELEMTYPE_UNKNOWN = 0
    IDH_ELEMTYPE_BOOLEAN = 1
    IDH_ELEMTYPE_SBYTE = 2
    IDH_ELEMTYPE_BYTE = 3
    IDH_ELEMTYPE_INT16 = 4
    IDH_ELEMTYPE_UINT16 = 5
    IDH_ELEMTYPE_INT32 = 6
    IDH_ELEMTYPE_UINT32 = 7
    IDH_ELEMTYPE_INT64 = 8
    IDH_ELEMTYPE_UINT64 = 9
    IDH_ELEMTYPE_FLOAT = 10
    IDH_ELEMTYPE_DOUBLE = 11

class IDH_QUALITY(Enum):
    # High 2-bit Quality Class
    IDH_HIGH_INVALID = 0x00    # 00xxxxxx
    IDH_HIGH_UNCERTAIN = 0x40  # 01xxxxxx
    IDH_HIGH_BAD = 0x80        # 10xxxxxx
    IDH_HIGH_GOOD = 0xC0       # 11xxxxxx
    IDH_HIGH_MASK = 0xC0

    # INVALID / BAD Base States (0x01–0x0F)
    IDH_LOW_INVALID_NODATA = 0x01       # BadNoData
    IDH_LOW_INVALID_UNREAD = 0x02       # BadWaitingForInitialData
    IDH_LOW_INVALID_UNSUBSCRIBE = 0x03  # BadNotConnected
    IDH_LOW_INVALID_TYPE = 0x04         # BadTypeMismatch
    IDH_LOW_INVALID_HANDLE = 0x05       # BadNodeIdUnknown / BadNodeIdInvalid
    IDH_LOW_INVALID_OVERFLOW = 0x06     # BadOutOfRange
    IDH_LOW_INVALID_BADVALUE = 0x07     # BadDataLost
    IDH_LOW_INVALID_BADQUALITY = 0x08   # BadUnexpectedError
    IDH_LOW_INVALID_TIMEOUT = 0x09      # BadTimeout
    IDH_LOW_INVALID_COMM = 0x0A         # BadCommunicationError
    IDH_LOW_INVALID_DEVICE = 0x0B       # BadDeviceFailure
    IDH_LOW_INVALID_CONFIG = 0x0C       # BadConfigurationError
    IDH_LOW_INVALID_LICENSE = 0x0D      # BadLicenseExpired
    IDH_LOW_INVALID_RESOURCE = 0x0E     # BadResourceUnavailable
    IDH_LOW_INVALID_INTERNAL = 0x0F     # BadInternalError

    # UNCERTAIN States (0x10–0x1F)
    IDH_LOW_UNCERTAIN_DATA = 0x10         # Uncertain
    IDH_LOW_UNCERTAIN_LASTVALUE = 0x11    # UncertainLastUsableValue
    IDH_LOW_UNCERTAIN_ESTIMATED = 0x12    # UncertainEstimatedValue
    IDH_LOW_UNCERTAIN_SUBSTITUTE = 0x13   # UncertainSubstituteValue
    IDH_LOW_UNCERTAIN_CALIBRATING = 0x14  # UncertainSensorNotAccurate
    IDH_LOW_UNCERTAIN_ENGUNIT = 0x15      # UncertainEngineeringUnitsExceeded
    IDH_LOW_UNCERTAIN_LOWDATA = 0x16      # UncertainDataSubNormal
    IDH_LOW_UNCERTAIN_HOLD = 0x17         # Hold last value
    IDH_LOW_UNCERTAIN_DERIVED = 0x18      # Derived value
    IDH_LOW_UNCERTAIN_SIMULATED = 0x19    # Simulated value
    IDH_LOW_UNCERTAIN_MANUALINPUT = 0x1A  # Manual input
    IDH_LOW_UNCERTAIN_TIMESYNC = 0x1B     # Time sync error
    IDH_LOW_UNCERTAIN_FILTERED = 0x1C     # Filtered value
    IDH_LOW_UNCERTAIN_PREPROCESS = 0x1D   # Preprocessed value
    IDH_LOW_UNCERTAIN_AGGREGATED = 0x1E   # Aggregated value
    IDH_LOW_UNCERTAIN_RESERVED = 0x1F

    # GOOD / LIMIT States (0x20–0x2F)
    IDH_LOW_GOOD_NORMAL = 0x20       # Good
    IDH_LOW_GOOD_HIGHLIMIT = 0x21    # GoodClamped - High limit
    IDH_LOW_GOOD_LOWLIMIT = 0x22     # GoodClamped - Low limit
    IDH_LOW_GOOD_HIGHHIGH = 0x23     # High alarm
    IDH_LOW_GOOD_LOWLOW = 0x24       # Low alarm
    IDH_LOW_GOOD_RATELIMIT = 0x25    # Rate limited
    IDH_LOW_GOOD_MANUAL = 0x26       # Manually entered
    IDH_LOW_GOOD_OVERRIDE = 0x27     # Manual override
    IDH_LOW_GOOD_BYPASS = 0x28       # Control bypass
    IDH_LOW_GOOD_MAINTENANCE = 0x29  # Maintenance mode
    IDH_LOW_GOOD_STARTUP = 0x2A      # Startup phase
    IDH_LOW_GOOD_SHUTDOWN = 0x2B     # Shutdown phase
    IDH_LOW_GOOD_WARMUP = 0x2C       # Warmup
    IDH_LOW_GOOD_STANDBY = 0x2D      # Standby
    IDH_LOW_GOOD_TESTMODE = 0x2E     # Test mode
    IDH_LOW_GOOD_SIMULATION = 0x2F   # Simulation mode

    # SYSTEM / PLATFORM ERRORS (0x30–0x3F)
    IDH_LOW_SYS_DBWRITEFAILED = 0x30  # Database write failed
    IDH_LOW_SYS_CACHEOVERFLOW = 0x31  # Cache overflow
    IDH_LOW_SYS_DISKFULL = 0x32       # Disk full
    IDH_LOW_SYS_PERMISSION = 0x33     # Permission denied
    IDH_LOW_SYS_PROTOCOL = 0x34       # Protocol error
    IDH_LOW_SYS_CODEC = 0x35          # Codec error
    IDH_LOW_SYS_CHECKSUM = 0x36       # Checksum error
    IDH_LOW_SYS_VERSION = 0x37        # Version mismatch
    IDH_LOW_SYS_DEPENDENCY = 0x38     # Dependency failed
    IDH_LOW_SYS_SERVICE = 0x39        # Service unavailable
    IDH_LOW_SYS_NODENOTFOUND = 0x3A   # Node not found
    IDH_LOW_SYS_TYPEMISMATCH = 0x3B   # Type mismatch
    IDH_LOW_SYS_ADDRINVALID = 0x3C    # Address invalid
    IDH_LOW_SYS_UNAUTHORIZED = 0x3D   # Unauthorized
    IDH_LOW_SYS_THROTTLED = 0x3E      # Throttled
    IDH_LOW_SYS_UNKNOWN = 0x3F         # Unknown error

class IDH_RTSOURCE_FLAG(Enum):
    IDH_RTSOURCE_FLAG_NONE = 0x0
    IDH_RTSOURCE_FLAG_SUBSCRIBE = 0x1 # support subscribe
    IDH_RTSOURCE_FLAG_RECONNECT = 0x2 # auto reconnect on connection lost

class IDH_RTSOURCE(Enum):
    IDH_RTSOURCE_UA = 0
    IDH_RTSOURCE_DA = 1
    IDH_RTSOURCE_CSV = 2
    IDH_RTSOURCE_MODBUS = 3
    IDH_RTSOURCE_COUNT = 4

class IDH_NODETYPE(Enum):
    IDH_NODETYPE_UNKNOWN = 0
    IDH_NODETYPE_OBJECT = 1
    IDH_NODETYPE_VARIABLE = 2
    IDH_NODETYPE_METHOD = 3
    IDH_NODETYPE_OBJECTTYPE = 4
    IDH_NODETYPE_VARIABLETYPE = 5
    IDH_NODETYPE_DATATYPE = 6
    IDH_NODETYPE_REFERENCETYPE = 7
    IDH_NODETYPE_VIEW = 8

class idh_source_desc_t(Structure):
    _fields_ = [
        ("source_type", c_uint),
        ("name", c_char * 256),
        ("schema", c_char * 256),
    ]

class idh_tag_t(Structure):
    _fields_ = [
        ("data_type", c_ushort),
        ("namespace_index", c_ushort),
        ("tag_name", c_char_p),
    ]

class idh_real_t(Structure):
    _fields_ = [
        ("value", c_double),            # value
        ("time_quality", c_ulonglong),  # [55:48]=quality, [48:0]=timestamp(ms since 2000-01-01)
    ]
    
    # Constants for time_quality field
    IDH_TQ_QUALITY_SHIFT = 48
    IDH_TQ_TIME_MASK = 0x0000FFFFFFFFFFFF
    
    def get_quality(self):
        """Extract quality from time_quality field"""
        return (self.time_quality >> self.IDH_TQ_QUALITY_SHIFT) & 0xFF

    @property
    def quality(self):
        return self.get_quality()
    
    def get_quality_high(self):
        """Extract high 2-bit quality class"""
        return self.get_quality() & IDH_QUALITY.IDH_HIGH_MASK.value

    def get_quality_low(self):
        """Extract low 6-bit quality class"""
        return self.get_quality() & ~IDH_QUALITY.IDH_HIGH_MASK.value

    def get_timestamp(self):
        """Extract timestamp from time_quality field (ms since 2000-01-01)"""
        return self.time_quality & self.IDH_TQ_TIME_MASK

    def get_timestamp_desc(self):
        """Get human-readable timestamp description"""
        timestamp_ms = self.get_timestamp()
        import datetime

        base_time = datetime.datetime(2000, 1, 1)
        max_delta = datetime.datetime.max - base_time
        max_supported_ms = (
            max_delta.days * 24 * 60 * 60 * 1000
            + max_delta.seconds * 1000
            + max_delta.microseconds // 1000
        )
        if timestamp_ms > max_supported_ms:
            return f"{timestamp_ms} ms since 2000-01-01"

        timestamp = base_time + datetime.timedelta(milliseconds=timestamp_ms)
        return timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    @property
    def timestamp(self):
        return self.get_timestamp()
    
    @staticmethod
    def make_time_quality(quality, timestamp_ms):
        """Create time_quality value from quality and timestamp"""
        return ((quality & 0xFF) << idh_real_t.IDH_TQ_QUALITY_SHIFT) | (timestamp_ms & idh_real_t.IDH_TQ_TIME_MASK)

    @staticmethod
    def get_high_quality_description(quality):
        """Get human-readable description of quality high"""
        high = quality & IDH_QUALITY.IDH_HIGH_MASK.value

        if high == IDH_QUALITY.IDH_HIGH_GOOD.value:
            return "Good"
        elif high == IDH_QUALITY.IDH_HIGH_UNCERTAIN.value:
            return "Uncertain"
        elif high == IDH_QUALITY.IDH_HIGH_BAD.value:
            return "Bad"
        else:
            return "Invalid"

class idh_browse_item_t(Structure):
    _fields_ = [
        ("namespace_index", c_ushort),
        ("node_name", c_char * 256),        # 节点名称
        ("display_name", c_char * 256),     # 显示名称
        ("description", c_char * 512),      # 节点描述
        ("node_type", c_int),               # IDH_NODETYPE
        ("data_type", c_int),               # IDH_DATATYPE
        ("is_readable", c_byte),            # 是否可读
        ("is_writable", c_byte),            # 是否可写
        ("has_children", c_byte),           # 是否有子节点
        ("value_rank", c_byte),             # IDH_VALUERANK_*, 占原来的尾部填充, 结构体大小不变
    ]

IDH_ARRAY_MAX_RANK = 4

# Arrays (idh_source_readarrays and friends). Elements are passed as double, and a
# multi-dimensional array is flattened row-major (the last index varies fastest).
class idh_array_t(Structure):
    _fields_ = [
        ("values", POINTER(c_double)),  # in: buffer for the elements, or NULL for the metadata only
        ("capacity", c_uint32),         # in: number of elements values can hold
        ("length", c_uint32),           # out: number of elements (the product of the dimensions)
        ("time_quality", c_ulonglong),  # out: same encoding as idh_real_t
        ("result", c_int32),            # out: 0, or a negative error code for this entry
        ("element_type", c_uint16),     # out: IDH_ELEMTYPE
        ("rank", c_uint8),              # out: number of dimensions; 0 for a scalar, read as one element
        ("reserved", c_uint8),
        ("dimensions", c_uint32 * IDH_ARRAY_MAX_RANK),  # out: dimension lengths, outermost first
    ]

class idh_array_value_t(Structure):
    _fields_ = [
        ("values", POINTER(c_double)),  # elements, row-major; may be NULL when length is 0
        ("length", c_uint32),           # number of elements
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
    c_uint,
]

# idh_source_valid
libidh.idh_source_valid.restype = c_int
libidh.idh_source_valid.argtypes = [idh_source_t]

# idh_source_set_sync_cache_msec
libidh.idh_source_set_sync_cache_msec.restype = c_int
libidh.idh_source_set_sync_cache_msec.argtypes = [idh_source_t, c_int]

# idh_source_get_sync_cache_msec
libidh.idh_source_get_sync_cache_msec.restype = c_int
libidh.idh_source_get_sync_cache_msec.argtypes = [idh_source_t]

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

# idh_group_clear
libidh.idh_group_clear.restype = None
libidh.idh_group_clear.argtypes = [idh_group_t]

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

# idh_source_readarrays
libidh.idh_source_readarrays.restype = c_int
libidh.idh_source_readarrays.argtypes = [
    idh_source_t,
    POINTER(idh_array_t),
    POINTER(idh_tag_t),
    POINTER(c_char_p),  # index_ranges, may be NULL
    c_int,
]

# idh_source_writearrays
libidh.idh_source_writearrays.restype = c_int
libidh.idh_source_writearrays.argtypes = [
    idh_source_t,
    POINTER(c_int),
    POINTER(idh_array_value_t),
    POINTER(idh_tag_t),
    POINTER(c_char_p),  # index_ranges, may be NULL
    c_int,
]

# idh_group_readarrays
libidh.idh_group_readarrays.restype = c_int
libidh.idh_group_readarrays.argtypes = [
    idh_group_t,
    POINTER(idh_array_t),
    POINTER(c_longlong),
    c_uint,
]

# idh_group_writearrays
libidh.idh_group_writearrays.restype = c_int
libidh.idh_group_writearrays.argtypes = [
    idh_group_t,
    POINTER(c_int),
    POINTER(idh_array_value_t),
    POINTER(c_longlong),
    c_uint,
]

# idh_source_browse
libidh.idh_source_browse.restype = c_int
libidh.idh_source_browse.argtypes = [idh_source_t, POINTER(idh_browse_item_t), POINTER(c_uint), c_ushort, c_char_p]

# idh_source_browse_root
libidh.idh_source_browse_root.restype = c_int
libidh.idh_source_browse_root.argtypes = [idh_source_t, POINTER(idh_browse_item_t), POINTER(c_uint)]

# 设置函数签名
libidh.idh_set_log_level.restype = c_int
libidh.idh_set_log_level.argtypes = [c_int]

libidh.idh_get_log_level.restype = c_int
libidh.idh_get_log_level.argtypes = [POINTER(c_int)]

# An entry whose buffer was too small (IDH_ERROR_SHRTLEN) is read again with the length the
# library reported. The array can grow again in between, so this is tried a few times in all.
_ARRAY_READ_ATTEMPTS = 3

def _tag_array(tags):
    tag_array = (idh_tag_t * len(tags))()
    for i, tag in enumerate(tags):
        tag_array[i].data_type = tag['data_type']
        tag_array[i].namespace_index = tag['namespace_index']
        tag_array[i].tag_name = tag['tag_name'].encode('utf-8')
    return tag_array

def _index_range_array(index_ranges, size):
    """None, or one OPC UA NumericRange string per tag; None or "" means the whole array."""
    if index_ranges is None:
        return None
    if len(index_ranges) != size:
        raise ValueError("index_ranges needs one entry per tag")
    return (c_char_p * size)(*[r.encode('utf-8') if r else None for r in index_ranges])

def _array_values(arrays):
    """idh_array_value_t entries for the arrays to write, plus the buffers they point into, which
    the caller keeps alive during the call. An array is a flat sequence of numbers, or anything
    with ravel(), such as a numpy array, which is flattened row-major."""
    values = (idh_array_value_t * len(arrays))()
    buffers = []
    for i, array in enumerate(arrays):
        if hasattr(array, 'ravel'):
            array = array.ravel()
        elements = [float(v) for v in array]
        buffer = (c_double * len(elements))(*elements)
        buffers.append(buffer)
        values[i].values = cast(buffer, POINTER(c_double)) if elements else None
        values[i].length = len(elements)
    return values, buffers

def _failed_results(size):
    """Write results that start as IDH_ERRCODE_FAILED, as libidh sets them once the arguments are
    valid: a call that fails earlier, such as on an invalid handle, leaves them alone."""
    return (c_int * size)(*([IDH_ERRCODE.IDH_ERRCODE_FAILED.value] * size))

def _array_entry(array, buffer, as_numpy):
    """One read entry as a dict. 'values' holds the elements only when 'result' is 0."""
    rank = array.rank
    dimensions = [array.dimensions[d] for d in range(min(rank, IDH_ARRAY_MAX_RANK))]
    values = list(buffer[:array.length]) if array.result == 0 and buffer is not None else []
    if as_numpy:
        import numpy
        values = numpy.array(values, dtype=numpy.float64)
        # A scalar or a one-dimensional array stays flat; deeper ranks keep their shape when
        # every dimension is known
        if array.result == 0 and 1 < rank <= IDH_ARRAY_MAX_RANK:
            values = values.reshape(dimensions)
    return {
        'result': array.result,
        'values': values,
        'length': array.length,
        'element_type': IDH_ELEMTYPE(array.element_type),
        'rank': rank,
        'dimensions': dimensions,
        'time_quality': array.time_quality,
        'quality': (array.time_quality >> idh_real_t.IDH_TQ_QUALITY_SHIFT) & 0xFF,
        'timestamp': array.time_quality & idh_real_t.IDH_TQ_TIME_MASK,
    }

def _read_arrays(read, count, capacity, as_numpy):
    """read(positions, arrays) runs the C read for the entries at positions. Returns the number of
    entries read, or the first call's negative error code, and one dict per entry."""
    capacities = [max(int(capacity), 0)] * count
    entries = [None] * count
    positions = list(range(count))
    ret = None
    for _ in range(_ARRAY_READ_ATTEMPTS):
        arrays = (idh_array_t * len(positions))()
        buffers = []
        for k, i in enumerate(positions):
            # No buffer at capacity 0: values is NULL, which libidh takes as "report the
            # metadata only", so no pointer to a zero-length ctypes array is handed out
            buffer = (c_double * capacities[i])() if capacities[i] else None
            buffers.append(buffer)
            arrays[k].values = cast(buffer, POINTER(c_double)) if buffer is not None else None
            arrays[k].capacity = capacities[i]
            # Start where libidh resets an entry (FAILED, INVALID|NODATA): it returns an invalid
            # handle before the reset, and a zeroed entry would read as an empty success
            arrays[k].result = IDH_ERRCODE.IDH_ERRCODE_FAILED.value
            arrays[k].time_quality = idh_real_t.make_time_quality(
                IDH_QUALITY.IDH_HIGH_INVALID.value | IDH_QUALITY.IDH_LOW_INVALID_NODATA.value, 0)
        r = read(positions, arrays)
        if ret is not None and r < 0:
            break  # a retry failed as a whole: those entries keep IDH_ERROR_SHRTLEN
        for k, i in enumerate(positions):
            if buffers[k] is None and arrays[k].result == 0 and arrays[k].length > 0:
                # A metadata-only read succeeds without the elements: the entry needs a
                # buffer of 'length' elements, the same as one whose buffer was too short
                arrays[k].result = IDH_ERRCODE.IDH_ERROR_SHRTLEN.value
            entries[i] = _array_entry(arrays[k], buffers[k], as_numpy)
        if ret is None:
            ret = r
            if r < 0:
                return r, entries
        positions = [i for i in positions
                     if entries[i]['result'] == IDH_ERRCODE.IDH_ERROR_SHRTLEN.value]
        if not positions:
            break
        for i in positions:
            capacities[i] = entries[i]['length']
    return sum(1 for entry in entries if entry['result'] == 0), entries

class IDHLibrary:
    def __init__(self):
        self.handle = libidh.idh_instance_create()
        if IDH_INVALID_HANDLE == self.handle:
            raise Exception("Failed to create IDH instance.")

    def destroy(self):
        if IDH_INVALID_HANDLE != self.handle:
            libidh.idh_instance_destroy(self.handle)
            self.handle = IDH_INVALID_HANDLE

    def set_log_level(self, level):
        """设置日志级别
        
        Args:
            level: IDH_LOG_LEVEL枚举值
            
        Returns:
            int: 成功返回0，失败返回错误码
        """
        if not isinstance(level, IDH_LOG_LEVEL):
            raise TypeError("level must be IDH_LOG_LEVEL enum")
        
        result = libidh.idh_set_log_level(level.value)
        return result

    def get_log_level(self):
        """获取当前日志级别
        
        Returns:
            IDH_LOG_LEVEL: 当前日志级别
        """
        level = c_int()
        result = libidh.idh_get_log_level(byref(level))
        if result == 0:
            return IDH_LOG_LEVEL(level.value)
        else:
            raise Exception(f"Failed to get log level, error code: {result}")

    def discovery(self, source_array, hostname="localhost", port=0):
        """Discover OPC Servers"""
        if not isinstance(source_array, list) or not all(isinstance(x, idh_source_desc_t) for x in source_array):
            raise TypeError("source_array must be a list of idh_source_desc_t")
        array = (idh_source_desc_t * len(source_array))(*source_array)
        result = libidh.idh_instance_discovery(
            self.handle,
            array,
            len(source_array),
            hostname.encode('utf-8'),
            port
        )
        # copy result back to source_array
        if result > 0:
            count = min(result, len(source_array))
            for i in range(count):
                source_array[i].source_type = array[i].source_type
                source_array[i].name = array[i].name
                source_array[i].schema = array[i].schema
        return result

    def create_source(self, source_type, source_schema, sample_timespan_msec, source_flag):
        return libidh.idh_source_create(
            self.handle,
            source_type,
            source_schema.encode('utf-8'),
            sample_timespan_msec,
            source_flag
        )

    def is_source_valid(self, source):
        return bool(libidh.idh_source_valid(source))

    def set_sync_cache_msec(self, source, msec):
        # 设置同步读模式(订阅时间为0)下的缓存有效窗口(毫秒), 默认100ms; 0=每次必读OPC
        return libidh.idh_source_set_sync_cache_msec(source, msec)

    def get_sync_cache_msec(self, source):
        # 获取当前同步读缓存窗口(毫秒); 返回>=0为窗口值, 负值为错误码
        return libidh.idh_source_get_sync_cache_msec(source)

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

    def clear_group(self, group):
        libidh.idh_group_clear(group)

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

    def read_arrays(self, source, tags, index_ranges=None, capacity=256, as_numpy=False):
        """
        Read arrays, one entry per tag (idh_source_readarrays). A scalar node is one element
        with rank 0.

        Args:
            source: source handle
            tags: tag dicts, as for read_values
            index_ranges: None, or one OPC UA NumericRange per tag ("3", "2:5", "0:1,2:3");
                None or "" reads the whole array
            capacity: elements to allocate per entry at first. An entry that needs more
                (IDH_ERROR_SHRTLEN) is read again with the length the library reported, so 0
                sizes every buffer from a first, metadata-only pass
            as_numpy: give 'values' as numpy float64 arrays, shaped like 'dimensions' for
                multi-dimensional arrays (needs numpy)

        Returns:
            tuple: (number of entries read, or a negative error code when the whole call failed;
                    one dict per tag with 'result', 'values' (empty unless 'result' is 0),
                    'length', 'element_type' (IDH_ELEMTYPE), 'rank', 'dimensions',
                    'time_quality', 'quality' and 'timestamp' (ms since 2000-01-01))
        """
        def read(positions, arrays):
            ranges = None if index_ranges is None else [index_ranges[i] for i in positions]
            return libidh.idh_source_readarrays(
                source,
                arrays,
                _tag_array([tags[i] for i in positions]),
                _index_range_array(ranges, len(positions)),
                len(positions)
            )

        if index_ranges is not None and len(index_ranges) != len(tags):
            raise ValueError("index_ranges needs one entry per tag")
        return _read_arrays(read, len(tags), capacity, as_numpy)

    def write_arrays(self, source, tags, arrays, index_ranges=None):
        """
        Write arrays, one per tag (idh_source_writearrays).

        Args:
            source: source handle
            tags: tag dicts, as for write_values
            arrays: one array per tag: a flat sequence of numbers in row-major order, or a
                numpy array, which is flattened row-major
            index_ranges: None, or one OPC UA NumericRange per tag; OPC DA rejects ranges

        Returns:
            tuple: (number of entries written; for a single entry that failed, its error code;
                    one result per tag)
        """
        if len(arrays) != len(tags):
            raise ValueError("arrays needs one entry per tag")
        values, buffers = _array_values(arrays)
        results = _failed_results(len(tags))
        result = libidh.idh_source_writearrays(
            source,
            results,
            values,
            _tag_array(tags),
            _index_range_array(index_ranges, len(tags)),
            len(tags)
        )
        return result, list(results)

    def read_group_arrays(self, group, handles, capacity=256, as_numpy=False):
        """
        Read arrays of subscribed tags (idh_group_readarrays), from the group's cache as
        read_group_values does. Arguments and result as for read_arrays, without index ranges.
        """
        def read(positions, arrays):
            sub_handles = (c_longlong * len(positions))(*[handles[i] for i in positions])
            return libidh.idh_group_readarrays(group, arrays, sub_handles, len(positions))

        return _read_arrays(read, len(handles), capacity, as_numpy)

    def write_group_arrays(self, group, handles, arrays):
        """
        Write arrays of subscribed tags (idh_group_writearrays), one per handle. Arguments and
        result as for write_arrays, without index ranges.
        """
        if len(arrays) != len(handles):
            raise ValueError("arrays needs one entry per handle")
        values, buffers = _array_values(arrays)
        handles_array = (c_longlong * len(handles))(*handles)
        results = _failed_results(len(handles))
        result = libidh.idh_group_writearrays(
            group,
            results,
            values,
            handles_array,
            len(handles)
        )
        return result, list(results)

    def browse_source(self, source, max_items, parent_namespace_index=0, parent_node_name=None):
        """
        browse opc tags
        
        Args:
            source: handle
            max_items: maxium items returned
            parent_namespace_index: namespace (ua)
            parent_node_name: parent，None if root
            
        Returns:
            tuple: (entry count, or IDH_ERRCODE_NOVALUE if there are no children, or another
                    negative error code; item list, empty when the code is negative)
        """
        items_array_type = idh_browse_item_t * max_items
        items_array = items_array_type()
        items_count = c_uint(max_items)
        
        parent_name_bytes = None
        if parent_node_name:
            parent_name_bytes = parent_node_name.encode('utf-8')
        
        result = libidh.idh_source_browse(
            source, 
            items_array, 
            byref(items_count),
            parent_namespace_index,
            parent_name_bytes
        )
        
        if result < 0:
            # A failed call may not have written items_count, which then still holds max_items.
            return result, []

        items_list = []
        for i in range(items_count.value):
            item = items_array[i]
            items_list.append({
                'namespace_index': item.namespace_index,
                'node_name': item.node_name.decode('utf-8') if item.node_name else '',
                'display_name': item.display_name.decode('utf-8') if item.display_name else '',
                'description': item.description.decode('utf-8') if item.description else '',
                'node_type': IDH_NODETYPE(item.node_type),
                'data_type': IDH_DATATYPE(item.data_type),
                'is_readable': bool(item.is_readable),
                'is_writable': bool(item.is_writable),
                'has_children': bool(item.has_children),
                'value_rank': item.value_rank
            })
        
        return result, items_list

    def browse_source_root(self, source, max_items):
        """
        浏览OPC服务器根目录
        
        Args:
            source: 数据源句柄
            max_items: 最大返回项目数量
            
        Returns:
            tuple: (条目数, 没有子节点时为 IDH_ERRCODE_NOVALUE, 其它负值为错误码; 浏览项目列表, 返回负值时为空)
        """
        items_array_type = idh_browse_item_t * max_items
        items_array = items_array_type()
        items_count = c_uint(max_items)
        
        result = libidh.idh_source_browse_root(
            source, 
            items_array, 
            byref(items_count)
        )
        
        if result < 0:
            # A failed call may not have written items_count, which then still holds max_items.
            return result, []

        items_list = []
        for i in range(items_count.value):
            item = items_array[i]
            items_list.append({
                'namespace_index': item.namespace_index,
                'node_name': item.node_name.decode('utf-8') if item.node_name else '',
                'display_name': item.display_name.decode('utf-8') if item.display_name else '',
                'description': item.description.decode('utf-8') if item.description else '',
                'node_type': IDH_NODETYPE(item.node_type),
                'data_type': IDH_DATATYPE(item.data_type),
                'is_readable': bool(item.is_readable),
                'is_writable': bool(item.is_writable),
                'has_children': bool(item.has_children),
                'value_rank': item.value_rank
            })
        
        return result, items_list

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
        source_flag=IDH_RTSOURCE_FLAG.IDH_RTSOURCE_FLAG_SUBSCRIBE.value
    )
    if IDH_INVALID_HANDLE == source:
        print("Failed to create source.")
        idh.destroy()
        return
    if not idh.is_source_valid(source):
        print("Source is not valid.")
        idh.destroy_source(source)
        idh.destroy()
        return

    # Browse example - browse root
    print("\n=== browse root ===")
    browse_result, browse_items = idh.browse_source_root(source, 50)
    print(f"Browse Root Result: {browse_result}")
    for item in browse_items[:10]:  # 只显示前10个项目
        print(f"  {item['node_name']} ({item['display_name']}) - Type: {item['node_type']}, "
              f"Readable: {item['is_readable']}, Writable: {item['is_writable']}, "
              f"Has Children: {item['has_children']}")
    
    # browse first child if it has
    for item in browse_items:
        if item['has_children'] and item['node_type'] == IDH_NODETYPE.IDH_NODETYPE_OBJECT:
            print(f"\n=== browse sub itme: {item['node_name']} ===")
            child_result, child_items = idh.browse_source(
                source, 20, item['namespace_index'], item['node_name']
            )
            print(f"Browse Child Result: {child_result}")
            for child in child_items[:5]: 
                print(f"    {child['node_name']} ({child['display_name']}) - Type: {child['node_type']}, "
                      f"Readable: {child['is_readable']}, Writable: {child['is_writable']}")
            break

    # Read values example
    tags = [
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 3, "tag_name": "Demo.Dynamic.Scalar.Float"},
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 3, "tag_name": "Demo.Dynamic.Scalar.Int32"},
    ]

    read_result, values = idh.read_values(source, tags)
    print(f"Read Result: {read_result}")
    for value in values:
        quality = value.get_quality()
        timestamp = value.get_timestamp()
        print(f"Quality: {quality}, Timestamp: {timestamp}, Value: {value.value}")

    # Write values example
    write_values = [123.456, 789.012]
    write_result, results = idh.write_values(source, tags, write_values)
    print(f"Write Result: {write_result}, Results: {results}")

    # Batch operations example
    group = idh.create_group(source, "Group1")
    if IDH_INVALID_HANDLE == group:
        print("Failed to create group.")
        idh.destroy_source(source)
        idh.destroy()
        return
    subscribe_result, handles = idh.subscribe_group(group, tags)
    # hex print handles
    handles_hex = [hex(handle) for handle in handles]
    print(f"Subscribe Result: {subscribe_result}, Handles: {handles_hex}")

    # Read group values
    group_read_result, group_values = idh.read_group_values(group, handles)
    print(f"Group Read Result: {group_read_result}")
    for value in group_values:
        quality = value.get_quality()
        timestamp = value.get_timestamp()
        print(f"Group Quality: {quality}, Group Timestamp: {timestamp}, Group Value: {value.value}")

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
