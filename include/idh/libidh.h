#pragma once

/* libidh : Industry Data Hub Library
 *  This library is used to provide a common interface for accessing data from different data
 * sources The data sources can be OPC UA, OPC DA, SQL, etc.
 * Note:
 * 1. Values are passed as double, which holds every integer up to 2^53 exactly. An Int64/UInt64
 *    value whose magnitude exceeds 2^53 is read as the nearest double; if the server reported it
 *    as good, its quality becomes IDH_HIGH_UNCERTAIN | IDH_LOW_UNCERTAIN_ESTIMATED.
 * 2. Minimal support OPC DA 2.0.
 * 3. DA Schema: opc.da://{hostname}/{ProgID}?ds_device=1 opc.da://{hostname}/{CLSID}?ds_device=0
 * 4. Modbus TCP Schema: modbus.tcp://{host}[:{port}][?key=value&...], port 502 by default.
 *    A tag's namespace_index is the unit id (0..255) and its tag_name is
 *    <co|di|ir|hr><address>[.<bit>][:<type>][@<word order>], with a 0-based address, e.g.
 *    hr100:f32@cdab or hr10.3. Types: bool i16 u16 i32 u32 i64 u64 f32 f64; word orders: abcd
 *    cdab badc dcba.
 */

#ifdef _WIN32
#    ifdef LIBIDH_EXPORTS
#        define LIBIDH_API __declspec(dllexport)
#    else
#        define LIBIDH_API __declspec(dllimport)
#    endif
#else
#    define LIBIDH_API
#endif

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef ZCE_DEFINED_LOGLEVEL
typedef enum _zlog_level {
    ZLOG_TRACE = 0,
    ZLOG_DEBUG = 1, /* debug */
    ZLOG_INFOR = 2, /* info */
    ZLOG_WARNI = 3, /* warn */
    ZLOG_ERROR = 4, /* error */
    ZLOG_FATAL = 5, /* fatal */
    ZLOG_BIZDT = 6, /* bizdata */
    ZLOG_NONEL = 7, /* none */
} ZLOG_LEVEL;
#    define ZCE_DEFINED_LOGLEVEL
#endif

/* Error codes use signed int values, matching the C API: compare results as int.
 * The 32-bit error bit patterns are preserved; conversion to long long sign-extends
 * negative errors, including entries in group handle/result arrays.
 */
#if defined(__cplusplus)
typedef enum _IDH_ERRCODE : int {
#else
typedef enum _IDH_ERRCODE {
#endif
    IDH_ERRCODE_SUCCESS = 0,

    IDH_SUCCEED_IDHBASE = 0x1110000,
    IDH_SUCCEED_ALREADYEXIST,

    IDH_ERRCODE_FAILED = -1,

    IDH_ERROR_COMMON = (int)0x81010000,  // IDH COMM ERROR
    IDH_ERROR_MALLOC,
    IDH_ERROR_UNSUPPORT,
    IDH_ERROR_SHRTLEN,
    IDH_ERROR_EXCDLEN,
    IDH_ERROR_CORRUPT,
    IDH_ERROR_SYNTAX,
    IDH_ERROR_ZIP,
    IDH_ERROR_TIMEOUT,
    IDH_ERROR_CONVERTOR,
    IDH_ERROR_CLOSED,
    IDH_ERROR_TOCLOSE,
    IDH_ERROR_PREVNULL,
    IDH_ERROR_OVERFLOW,
    IDH_ERROR_INVALID,
    IDH_ERROR_DUPLICATED,
    IDH_ERROR_UNINIT,
    IDH_ERROR_BADPRC,
    IDH_ERROR_NORESOURCE,
    IDH_ERROR_VERSION,

    IDH_ERRCODE_IDHBASE = (int)0x81110000,
    IDH_ERRCODE_INVALIDTAG,
    IDH_ERRCODE_INVALIDHANDLE,
    IDH_ERRCODE_INVALIDSERVER,
    IDH_ERRCODE_ADDITEM,
    IDH_ERRCODE_NOVALUE,
    IDH_ERRCODE_BADQUANLITY,
    IDH_ERRCODE_UNSUPPORTTYPE,
    IDH_ERRCODE_UNSUBSCRIBED,
    IDH_ERRCODE_NOTALLREADABLE,
    IDH_ERRCODE_HASUNSUBSRIBEDITEM,  // group operation has unsubscribed item
    IDH_ERRCODE_SUBSCRIBEFAILED,
    IDH_ERRCODE_INCONSISTENT,  // inconsistent request, e.g. write different values for the same tag
    IDH_ERRCODE_BADSROUCE,

} IDH_ERRCODE;

typedef enum _IDH_DATATYPE {
    IDH_DATATYPE_UNKNOW = 0,
    IDH_DATATYPE_REAL = 1,
    IDH_DATATYPE_TIMESTAMP = 2,
    IDH_DATATYPE_STRING = 3,
} IDH_DATATYPE;

/* Element type of an array value, see idh_array_t::element_type. */
typedef enum _IDH_ELEMTYPE {
    IDH_ELEMTYPE_UNKNOWN = 0,
    IDH_ELEMTYPE_BOOLEAN = 1,
    IDH_ELEMTYPE_SBYTE = 2,
    IDH_ELEMTYPE_BYTE = 3,
    IDH_ELEMTYPE_INT16 = 4,
    IDH_ELEMTYPE_UINT16 = 5,
    IDH_ELEMTYPE_INT32 = 6,
    IDH_ELEMTYPE_UINT32 = 7,
    IDH_ELEMTYPE_INT64 = 8,
    IDH_ELEMTYPE_UINT64 = 9,
    IDH_ELEMTYPE_FLOAT = 10,
    IDH_ELEMTYPE_DOUBLE = 11,
} IDH_ELEMTYPE;

typedef enum _IDH_QUALITY {
    /* ---------------- High 2-bit Quality Class ---------------- */
    IDH_HIGH_INVALID = 0x00,    // 00xxxxxx
    IDH_HIGH_UNCERTAIN = 0x40,  // 01xxxxxx
    IDH_HIGH_BAD = 0x80,        // 10xxxxxx
    IDH_HIGH_GOOD = 0xC0,       // 11xxxxxx
    IDH_HIGH_MASK = 0xC0,
    IDH_LOW_MASK = 0x3F,

    /* ---------------- INVALID / BAD Base States (0x01–0x0F) ---------------- */
    IDH_LOW_INVALID_NODATA = 0x01,       // BadNoData
    IDH_LOW_INVALID_UNREAD = 0x02,       // BadWaitingForInitialData
    IDH_LOW_INVALID_UNSUBSCRIBE = 0x03,  // BadNotConnected
    IDH_LOW_INVALID_TYPE = 0x04,         // BadTypeMismatch
    IDH_LOW_INVALID_HANDLE = 0x05,       // BadNodeIdUnknown / BadNodeIdInvalid
    IDH_LOW_INVALID_OVERFLOW = 0x06,     // BadOutOfRange
    IDH_LOW_INVALID_BADVALUE = 0x07,     // BadDataLost
    IDH_LOW_INVALID_BADQUALITY = 0x08,   // BadUnexpectedError
    IDH_LOW_INVALID_TIMEOUT = 0x09,      // BadTimeout
    IDH_LOW_INVALID_COMM = 0x0A,         // BadCommunicationError
    IDH_LOW_INVALID_DEVICE = 0x0B,       // BadDeviceFailure
    IDH_LOW_INVALID_CONFIG = 0x0C,       // BadConfigurationError
    IDH_LOW_INVALID_LICENSE = 0x0D,      // BadLicenseExpired
    IDH_LOW_INVALID_RESOURCE = 0x0E,     // BadResourceUnavailable
    IDH_LOW_INVALID_INTERNAL = 0x0F,     // BadInternalError

    /* ---------------- UNCERTAIN States (0x10–0x1F) ---------------- */
    IDH_LOW_UNCERTAIN_DATA = 0x10,         // Uncertain
    IDH_LOW_UNCERTAIN_LASTVALUE = 0x11,    // UncertainLastUsableValue
    IDH_LOW_UNCERTAIN_ESTIMATED = 0x12,    // UncertainEstimatedValue
    IDH_LOW_UNCERTAIN_SUBSTITUTE = 0x13,   // UncertainSubstituteValue
    IDH_LOW_UNCERTAIN_CALIBRATING = 0x14,  // UncertainSensorNotAccurate
    IDH_LOW_UNCERTAIN_ENGUNIT = 0x15,      // UncertainEngineeringUnitsExceeded
    IDH_LOW_UNCERTAIN_LOWDATA = 0x16,      // UncertainDataSubNormal
    IDH_LOW_UNCERTAIN_HOLD = 0x17,         // Hold last value
    IDH_LOW_UNCERTAIN_DERIVED = 0x18,      // Derived value
    IDH_LOW_UNCERTAIN_SIMULATED = 0x19,    // Simulated value
    IDH_LOW_UNCERTAIN_MANUALINPUT = 0x1A,  // Manual input
    IDH_LOW_UNCERTAIN_TIMESYNC = 0x1B,     // Time sync error
    IDH_LOW_UNCERTAIN_FILTERED = 0x1C,     // Filtered value
    IDH_LOW_UNCERTAIN_PREPROCESS = 0x1D,   // Preprocessed value
    IDH_LOW_UNCERTAIN_AGGREGATED = 0x1E,   // Aggregated value
    IDH_LOW_UNCERTAIN_RESERVED = 0x1F,

    /* ---------------- GOOD / LIMIT States (0x20–0x2F) ---------------- */
    IDH_LOW_GOOD_NORMAL = 0x20,       // Good
    IDH_LOW_GOOD_HIGHLIMIT = 0x21,    // GoodClamped - High limit
    IDH_LOW_GOOD_LOWLIMIT = 0x22,     // GoodClamped - Low limit
    IDH_LOW_GOOD_HIGHHIGH = 0x23,     // High alarm
    IDH_LOW_GOOD_LOWLOW = 0x24,       // Low alarm
    IDH_LOW_GOOD_RATELIMIT = 0x25,    // Rate limited
    IDH_LOW_GOOD_MANUAL = 0x26,       // Manually entered
    IDH_LOW_GOOD_OVERRIDE = 0x27,     // Manual override
    IDH_LOW_GOOD_BYPASS = 0x28,       // Control bypass
    IDH_LOW_GOOD_MAINTENANCE = 0x29,  // Maintenance mode
    IDH_LOW_GOOD_STARTUP = 0x2A,      // Startup phase
    IDH_LOW_GOOD_SHUTDOWN = 0x2B,     // Shutdown phase
    IDH_LOW_GOOD_WARMUP = 0x2C,       // Warmup
    IDH_LOW_GOOD_STANDBY = 0x2D,      // Standby
    IDH_LOW_GOOD_TESTMODE = 0x2E,     // Test mode
    IDH_LOW_GOOD_SIMULATION = 0x2F,   // Simulation mode

    /* ---------------- SYSTEM / PLATFORM ERRORS (0x30–0x3F) ---------------- */
    IDH_LOW_SYS_DBWRITEFAILED = 0x30,  // Database write failed
    IDH_LOW_SYS_CACHEOVERFLOW = 0x31,  // Cache overflow
    IDH_LOW_SYS_DISKFULL = 0x32,       // Disk full
    IDH_LOW_SYS_PERMISSION = 0x33,     // Permission denied
    IDH_LOW_SYS_PROTOCOL = 0x34,       // Protocol error
    IDH_LOW_SYS_CODEC = 0x35,          // Codec error
    IDH_LOW_SYS_CHECKSUM = 0x36,       // Checksum error
    IDH_LOW_SYS_VERSION = 0x37,        // Version mismatch
    IDH_LOW_SYS_DEPENDENCY = 0x38,     // Dependency failed
    IDH_LOW_SYS_SERVICE = 0x39,        // Service unavailable
    IDH_LOW_SYS_NODENOTFOUND = 0x3A,   // Node not found
    IDH_LOW_SYS_TYPEMISMATCH = 0x3B,   // Type mismatch
    IDH_LOW_SYS_ADDRINVALID = 0x3C,    // Address invalid
    IDH_LOW_SYS_UNAUTHORIZED = 0x3D,   // Unauthorized
    IDH_LOW_SYS_THROTTLED = 0x3E,      // Throttled
    IDH_LOW_SYS_UNKNOWN = 0x3F         // Unknown error

} IDH_QUALITY;

static int idh_is_good_quality(uint8_t quality) {
    return (quality & IDH_HIGH_MASK) == IDH_HIGH_GOOD;
}

static const long long IDH_INVALID_HANDLE = ~0;

typedef enum _IDH_RTSOURCE_FLAG {
    IDH_RTSOURCE_FLAG_NONE = 0x0,
    IDH_RTSOURCE_FLAG_SUBSCRIBE = 0x1,  // support subscribe
    IDH_RTSOURCE_FLAG_RECONNECT = 0x2,  // auto reconnect on connection lost
} IDH_RTSOURCE_FLAG;

typedef enum _IDH_RTSOURCE  {
    IDH_RTSOURCE_UA,
    IDH_RTSOURCE_DA,
    IDH_RTSOURCE_CSV,
    IDH_RTSOURCE_MODBUS,  // Modbus TCP, see note 4 at the top
    IDH_RTSOURCE_COUNT
} IDH_RTSOURCE;

typedef long long idh_handle_t;

typedef long long idh_source_t;

typedef struct _idh_source_desc {
    IDH_RTSOURCE source_type;
    char name[256];
    char schema[256];
} idh_source_desc_t;

typedef long long idh_group_t;

typedef struct _idh_tag {
    uint16_t data_type;
    uint16_t namespace_index;
    const char* tag_name;
} idh_tag_t;

typedef struct _idh_real {
    double value;           // value
    uint64_t time_quality;  // [55:48]=quality, [48:0]=timestamp(ms since 2000-01-01)
} idh_real_t;

#define IDH_TQ_QUALITY_SHIFT 48
#define IDH_TQ_TIME_MASK 0x0000FFFFFFFFFFFFULL

/* Arrays (idh_source_readarrays / idh_source_writearrays). Elements are passed as double, as
 * scalars are, and a multi-dimensional array is flattened row-major (the last index varies
 * fastest). One quality and one timestamp cover the whole array. */
#define IDH_ARRAY_MAX_RANK 4

typedef struct _idh_array {
    double* values;         // in: buffer for the elements, or NULL to report only the metadata
    uint32_t capacity;      // in: number of elements values can hold
    uint32_t length;        // out: number of elements (the product of the dimensions)
    uint64_t time_quality;  // out: same encoding as idh_real_t
    int32_t result;         // out: 0, or a negative error code for this entry
    uint16_t element_type;  // out: IDH_ELEMTYPE
    uint8_t rank;           // out: number of dimensions; 0 for a scalar, read as one element
    uint8_t reserved;
    uint32_t dimensions[IDH_ARRAY_MAX_RANK];  // out: dimension lengths, outermost first; ranks
                                              //      above IDH_ARRAY_MAX_RANK report only these
} idh_array_t;

typedef struct _idh_array_value {
    const double* values;  // elements, row-major; may be NULL when length is 0
    uint32_t length;       // number of elements
} idh_array_value_t;

static inline uint8_t idh_get_quality(uint64_t tq) {
    return (uint8_t)(tq >> IDH_TQ_QUALITY_SHIFT);
}

static inline uint8_t idh_get_quality_high(uint64_t tq) {
    return (IDH_HIGH_MASK & (uint8_t)(tq >> IDH_TQ_QUALITY_SHIFT));
}

static inline uint8_t idh_get_quality_low(uint64_t tq) {
    return (IDH_LOW_MASK & (uint8_t)(tq >> IDH_TQ_QUALITY_SHIFT));
}

static inline uint64_t idh_get_timestamp(uint64_t tq) { return tq & IDH_TQ_TIME_MASK; }

static inline uint64_t idh_make_time_quality(uint8_t q, uint64_t ms) {
    return ((uint64_t)q << IDH_TQ_QUALITY_SHIFT) | (ms & IDH_TQ_TIME_MASK);
}

typedef enum _IDH_NODETYPE {
    IDH_NODETYPE_UNKNOWN = 0,
    IDH_NODETYPE_OBJECT = 1,
    IDH_NODETYPE_VARIABLE = 2,
    IDH_NODETYPE_METHOD = 3,
    IDH_NODETYPE_OBJECTTYPE = 4,
    IDH_NODETYPE_VARIABLETYPE = 5,
    IDH_NODETYPE_DATATYPE = 6,
    IDH_NODETYPE_REFERENCETYPE = 7,
    IDH_NODETYPE_VIEW = 8
} IDH_NODETYPE;

/* idh_browse_item_t::value_rank, the same values as the OPC UA ValueRank attribute. Any n >= 1 is
 * an array with exactly n dimensions; only 1 has a name below, and fixed ranks above 127 are
 * reported as 127. Only variables carry one; every other node reports IDH_VALUERANK_SCALAR. A
 * variable whose rank could not be read reports IDH_VALUERANK_ANY. */
#define IDH_VALUERANK_SCALAR_OR_ONE_DIMENSION (-3)
#define IDH_VALUERANK_ANY (-2)  // scalar or array of any rank, or unknown
#define IDH_VALUERANK_SCALAR (-1)
#define IDH_VALUERANK_ONE_OR_MORE_DIMENSIONS 0  // array, rank not fixed (OPC DA arrays)
#define IDH_VALUERANK_ONE_DIMENSION 1           // array with exactly one dimension

typedef struct _idh_browse_item {
    uint16_t namespace_index;
    char node_name[256];         // 节点名称
    char display_name[256];      // 显示名称
    char description[512];       // 节点描述
    IDH_NODETYPE node_type;      // 节点类型
    IDH_DATATYPE data_type;      // 数据类型（仅变量节点有效）; 数组节点为元素的类型
    uint8_t is_readable;   // 是否可读
    uint8_t is_writable;   // 是否可写
    uint8_t has_children;  // 是否有子节点
    int8_t value_rank;     // 标量还是数组, 见 IDH_VALUERANK_*. 占用原来的结构体尾部填充,
                           // sizeof 和其它字段的偏移都不变
} idh_browse_item_t;

LIBIDH_API idh_handle_t idh_instance_create();

LIBIDH_API void idh_instance_destroy(idh_handle_t handle);

// 日志级别设置函数
LIBIDH_API int idh_set_log_level(ZLOG_LEVEL level);

LIBIDH_API int idh_get_log_level(ZLOG_LEVEL* level);

LIBIDH_API int idh_instance_discovery(idh_handle_t handle, idh_source_desc_t* source_vec,
                                      unsigned source_size, const char* hostname,
                                      uint16_t port);
/* data source */

// sample_timespan_msec: 订阅周期(毫秒). >0 = 订阅模式(组读返回订阅缓存);
//   ==0 = 不订阅(同步读模式), 组读时直接同步读OPC并按缓存窗口节流
LIBIDH_API idh_source_t idh_source_create(idh_handle_t handle, IDH_RTSOURCE source_type,
                                          const char* source_schema, int sample_timespan_msec,
                                          unsigned int source_flag);

LIBIDH_API int idh_source_valid(idh_source_t source_id);

// 设置同步读模式(订阅时间为0)下的缓存有效窗口(毫秒), 默认100ms; 0 = 每次组读都同步读OPC.
// 窗口内的快读直接返回缓存, 避免大量请求打到OPC服务器. 返回0成功, 负值为错误码.
LIBIDH_API int idh_source_set_sync_cache_msec(idh_source_t source_id, int msec);

// 获取当前同步读缓存窗口(毫秒). 返回 >=0 为当前窗口值, 负值为错误码.
LIBIDH_API int idh_source_get_sync_cache_msec(idh_source_t source_id);

LIBIDH_API void idh_source_destroy(idh_source_t source_id);

LIBIDH_API int idh_source_browse(idh_source_t source_id, idh_browse_item_t* items,
                                 unsigned* items_count, uint16_t parent_namespace_index,
                                 const char* parent_node_name);

LIBIDH_API int idh_source_browse_root(idh_source_t source_id, idh_browse_item_t* items,
                                      unsigned* items_count);

LIBIDH_API int idh_source_readvalues(idh_source_t source_id, idh_real_t* values,
                                     const idh_tag_t* tags_ptr, int tags_size);

LIBIDH_API int idh_source_writevalues(idh_source_t source_id, int* results, const double* values,
                                      const idh_tag_t* tags_ptr, int tags_size);

/* Array read and write, OPC UA and OPC DA: other sources return IDH_ERROR_UNSUPPORT. The scalar
 * APIs above keep rejecting arrays.
 * index_ranges: NULL, or one entry per tag. An entry that is NULL or "" means the whole array;
 * otherwise it is an OPC UA NumericRange such as "3", "2:5" or "0:1,2:3". A single element is
 * written "2", not "2:2". OPC DA has no index ranges: a read applies the range locally, with the
 * same results as an OPC UA server; a write with a range is IDH_ERROR_UNSUPPORT for that entry.
 * OPC DA arrays are one-dimensional SAFEARRAYs.
 * Both return a negative error code when the whole call fails: IDH_ERRCODE_INVALIDHANDLE,
 * IDH_ERROR_INVALID (arrays/results, values or tags NULL, or tags_size <= 0), IDH_ERROR_UNSUPPORT,
 * or a connection failure. Once the arguments are valid, every entry's result is first set to
 * IDH_ERRCODE_FAILED, so a call that fails later still leaves defined entries. */

/* Returns the number of entries whose result is 0. Per entry:
 * - the elements fit: they are copied to values and result is 0;
 * - values is NULL: only length, element_type, rank, dimensions and time_quality are set;
 * - capacity is too small: result IDH_ERROR_SHRTLEN, length is the number needed and values is
 *   left untouched;
 * - Bad or Uncertain values are copied and counted; time_quality says what they are worth.
 *   Int64 and UInt64 elements beyond 2^53 turn GOOD into UNCERTAIN|ESTIMATED, as for scalars;
 * - IDH_ERRCODE_UNSUPPORTTYPE: the elements are not numbers or Booleans (strings, DateTime, ...);
 * - IDH_ERRCODE_NOVALUE: no value, or no element in the index range (a lower bound past the end,
 *   or more dimensions than the value). An upper bound past the end reads up to the end;
 * - IDH_ERROR_SYNTAX: a malformed index range, which is not sent, or one with fewer dimensions
 *   than the value;
 * - IDH_ERRCODE_INVALIDTAG: the node does not exist. */
LIBIDH_API int idh_source_readarrays(idh_source_t source_id, idh_array_t* arrays,
                                     const idh_tag_t* tags_ptr, const char* const* index_ranges,
                                     int tags_size);

/* Returns the number of entries written; for a single entry that failed, its error code. The node
 * is read first to learn its element type and shape, so a node that cannot be read is
 * IDH_ERRCODE_UNSUPPORTTYPE; OPC DA then uses the item's canonical type instead. Per entry,
 * nothing is sent when:
 * - any element cannot be represented in the element type (out of range, NaN or +-inf for an
 *   integer or Boolean, a finite value that would become +-inf in a Float): IDH_ERROR_OVERFLOW;
 * - an index range reaches past the end of the array (reads stop at the end, writes do not) or
 *   holds no element: IDH_ERROR_OVERFLOW;
 * - a scalar node (exactly one element), a multi-dimensional node or an index range gets a
 *   different number of elements than it holds: IDH_ERROR_SHRTLEN or IDH_ERROR_EXCDLEN. The
 *   length of a one-dimensional whole-array write is left to the server.
 * Server rejections: IDH_ERRCODE_UNSUPPORTTYPE (BadTypeMismatch, for example a fixed-length
 * array of another length), IDH_ERROR_OVERFLOW (BadOutOfRange, BadIndexRangeNoData),
 * IDH_ERRCODE_INVALIDTAG (unknown node), otherwise IDH_ERRCODE_FAILED. */
LIBIDH_API int idh_source_writearrays(idh_source_t source_id, int* results,
                                      const idh_array_value_t* values, const idh_tag_t* tags_ptr,
                                      const char* const* index_ranges, int tags_size);

/* batch operators. speed up for high frequency read/write */

LIBIDH_API idh_group_t idh_group_create(idh_source_t handle, const char* group_name);

LIBIDH_API void idh_group_clear(idh_group_t batch_id);

LIBIDH_API int idh_group_subscribe(idh_group_t batch_id, long long* handles_or_errcode,
                                   const idh_tag_t* tags_ptr, unsigned tags_size);

LIBIDH_API void idh_group_unsubscribe(idh_group_t batch_id, const long long* tag_handles,
                                      unsigned tags_size);

LIBIDH_API
int idh_group_readvalues(idh_group_t batch_id, idh_real_t* values_ptr, const long long* tag_handles,
                         unsigned tags_size);

LIBIDH_API int idh_group_writevalues(idh_group_t batch_id, int* results, const double* values_ptr,
                                     const long long* tag_handles, unsigned tags_size);

/* Array read and write for subscribed tags (handles from idh_group_subscribe), OPC UA and OPC
 * DA. They work as idh_source_readarrays / idh_source_writearrays without index ranges, which
 * a group does not keep; use the source calls for part of an array.
 * - Reads come from the group's cache, as idh_group_readvalues: the subscription, or with
 *   sample_timespan_msec == 0 a synchronous read throttled by the sync cache window.
 * - An invalid handle is IDH_ERRCODE_INVALIDHANDLE for that entry, with time_quality
 *   INVALID|HANDLE; a tag without a monitored item (OPC DA: an item not added to the group yet)
 *   is IDH_ERRCODE_UNSUBSCRIBED. When no handle is valid the call returns
 *   IDH_ERRCODE_UNSUBSCRIBED.
 * - A write reads the node first for its element type and shape, as the source call does. A
 *   handle given more than once is written once with its last array; earlier entries with the
 *   same elements share its result, the others are IDH_ERROR_DUPLICATED, as in
 *   idh_group_writevalues. The next group read returns the written value. */
LIBIDH_API int idh_group_readarrays(idh_group_t batch_id, idh_array_t* arrays,
                                    const long long* tag_handles, unsigned tags_size);

LIBIDH_API int idh_group_writearrays(idh_group_t batch_id, int* results,
                                     const idh_array_value_t* values, const long long* tag_handles,
                                     unsigned tags_size);

LIBIDH_API void idh_group_destroy(idh_group_t batch_id);

#ifdef __cplusplus
}
#endif
