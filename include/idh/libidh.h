#pragma once

/* libidh : Industry Data Hub Library
 *  This library is used to provide a common interface for accessing data from different data
 * sources The data sources can be OPC UA, OPC DA, SQL, etc.
 * Note:
 * 1. Don't support abs(int64/uint64) >= 2^52, because of the precision of double.
 * 2. Minimal support OPC DA 2.0. opc.da://{hostname}/{ProgID} opc.da://{hostname}/{CLSID}
 */

#ifdef _WIN32
#    ifdef LIBIDH_EXPORTS
#        define LIBIDH_API __declspec(dllexport)
#    else
#        define LIBIDH_API __declspec(dllimport)
#        pragma comment(lib, "libidh.lib")
#    endif
#else
#    define LIBIDH_API
#endif

#ifdef __cplusplus
extern "C" {
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

    IDH_HIGH_INVALID = 0x0,
    IDH_HIGH_GOOD = 0x0100,
    IDH_HIGH_BAD = 0x0200,
    IDH_HIGH_UNCERTAIN = 0x0300,
    IDH_HIGH_MASK = 0xff00,

    IDH_LOW_INVALID_NODATA = 0x01,       // tag value not exists
    IDH_LOW_INVALID_UNREAD = 0x02,       // tag value has not been read
    IDH_LOW_INVALID_UNSUBSCRIBE = 0x03,  // batch operation has unsubscribed item
    IDH_LOW_INVALID_TYPE = 0x04,         // cannot convert data type
    IDH_LOW_INVALID_HANDLE = 0x05,       // bad quality
    IDH_LOW_INVALID_OVERFLOW = 0x06,     // overflow
    IDH_LOW_INVALID_BADVALUE = 0x07,     // bad value
    IDH_LOW_INVALID_BADQUALITY = 0x08,   // bad quality

    IDH_LOW_GOOD_MANUAL = 0x01,  // manually entered

} IDH_QUALITY;

static int idh_is_good_quality(unsigned short quality) {
    return (quality & IDH_HIGH_MASK) == IDH_HIGH_GOOD;
}

static const long long IDH_INVALID_HANDLE = ~0;

typedef enum _IDH_RTSOURCE { IDH_RTSOURCE_UA, IDH_RTSOURCE_DA, IDH_RTSOURCE_COUNT } IDH_RTSOURCE;

typedef long long idh_handle_t;

typedef long long idh_source_t;

typedef struct _idh_source_desc {
    IDH_RTSOURCE source_type;
    char name[256];
    char schema[256];
} idh_source_desc_t;

typedef long long idh_group_t;

typedef struct _idh_tag {
    unsigned char data_type;
    unsigned short namespace_index;
    const char* tag_name;
} idh_tag_t;

typedef struct _idh_real {
    unsigned short quality;  // IDH_QUALITY
    long long timestamp;     // million second from 1970-01-01 00:00:00
    double value;            // value
} idh_real_t;

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
    unsigned short namespace_index;
    char node_name[256];        // 节点名称
    char display_name[256];     // 显示名称
    char description[512];      // 节点描述
    IDH_NODETYPE node_type;     // 节点类型
    IDH_DATATYPE data_type;     // 数据类型（仅变量节点有效）
    unsigned char is_readable;  // 是否可读
    unsigned char is_writable;  // 是否可写
    unsigned char has_children; // 是否有子节点
} idh_browse_item_t;

LIBIDH_API idh_handle_t idh_instance_create();

LIBIDH_API void idh_instance_destroy(idh_handle_t handle);

LIBIDH_API int idh_instance_discovery(idh_handle_t handle, idh_source_desc_t* source_vec,
                                      unsigned source_size, const char* hostname,
                                      unsigned short port);
/* data source */

LIBIDH_API idh_source_t idh_source_create(idh_handle_t handle, IDH_RTSOURCE source_type,
                                          const char* source_schema, int sample_timespan_msec,
                                          int support_subscribe);

LIBIDH_API int idh_source_valid(idh_source_t source_id);

LIBIDH_API void idh_source_destroy(idh_source_t source_id);

LIBIDH_API int idh_source_browse(idh_source_t source_id, idh_browse_item_t* items,
                                 unsigned* items_count, unsigned short parent_namespace_index,
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
