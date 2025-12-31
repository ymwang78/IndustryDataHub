#pragma once

/* libidh : Industry Data Hub Library
 *  This library is used to provide a common interface for accessing data from different data
 * sources The data sources can be OPC UA, OPC DA, SQL, etc.
 * Note:
 * 1. Don't support abs(int64/uint64) >= 2^52, because of the precision of double.
 * 2. Minimal support OPC DA 2.0.
 * 3. DA Schema: opc.da://{hostname}/{ProgID}?ds_device=1 opc.da://{hostname}/{CLSID}?ds_device=0
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

typedef enum _IDH_ERRCODE {
    IDH_ERRCODE_SUCCESS = 0,

    IDH_SUCCEED_IDHBASE = 0x1110000,
    IDH_SUCCEED_ALREADYEXIST,

    IDH_ERRCODE_FAILED = -1,

    IDH_ERROR_COMMON = 0x81010000,  // IDH COMM ERROR
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

    IDH_ERRCODE_IDHBASE = 0x81110000,
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

typedef enum _IDH_QUALITY {
    /* ---------------- High 2-bit Quality Class ---------------- */
    IDH_HIGH_INVALID = 0x00,    // 00xxxxxx
    IDH_HIGH_UNCERTAIN = 0x40,  // 01xxxxxx
    IDH_HIGH_BAD = 0x80,        // 10xxxxxx
    IDH_HIGH_GOOD = 0xC0,       // 11xxxxxx
    IDH_HIGH_MASK = 0xC0,

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

typedef enum _IDH_RTSOURCE : uint8_t {
    IDH_RTSOURCE_UA,
    IDH_RTSOURCE_DA,
    IDH_RTSOURCE_CSV,
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

static inline uint8_t idh_get_quality(uint64_t tq) {
    return (uint8_t)(tq >> IDH_TQ_QUALITY_SHIFT);
}

static inline uint8_t idh_get_quality_high(uint64_t tq) {
    return (IDH_HIGH_MASK & (uint8_t)(tq >> IDH_TQ_QUALITY_SHIFT));
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

typedef struct _idh_browse_item {
    uint16_t namespace_index;
    char node_name[256];         // 节点名称
    char display_name[256];      // 显示名称
    char description[512];       // 节点描述
    IDH_NODETYPE node_type;      // 节点类型
    IDH_DATATYPE data_type;      // 数据类型（仅变量节点有效）
    uint8_t is_readable;   // 是否可读
    uint8_t is_writable;   // 是否可写
    uint8_t has_children;  // 是否有子节点
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

LIBIDH_API idh_source_t idh_source_create(idh_handle_t handle, IDH_RTSOURCE source_type,
                                          const char* source_schema, int sample_timespan_msec,
                                          unsigned int source_flag);

LIBIDH_API int idh_source_valid(idh_source_t source_id);

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

LIBIDH_API void idh_group_destroy(idh_group_t batch_id);

#ifdef __cplusplus
}
#endif
