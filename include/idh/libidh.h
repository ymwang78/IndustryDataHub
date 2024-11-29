#pragma once

/* libidh : Industry Data Hub Library
 *  This library is used to provide a common interface for accessing data from different data
 * sources The data sources can be OPC UA, OPC DA, SQL, etc.
 * Note:
 * 1. Don't support abs(int64/uint64) >= 2^52
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
    IDH_ERRCODE_FAILED = -1,
    IDH_ERRCODE_ERRBASE = 0x81110000,
    IDH_ERRCODE_INVALIDHANDLE,
    IDH_ERRCODE_NOVALUE,
    IDH_ERRCODE_BADQUANLITY,
    IDH_ERRCODE_UNSUPPORTTYPE,
    IDH_ERRCODE_NOTALLREADABLE,
    IDH_ERRCODE_HASUNSUBSRIBEDITEM,  // batch operation has unsubscribed item
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

} IDH_QUALITY;

typedef enum _IDH_RTSOURCE { IDH_RTSOURCE_UA, IDH_RTSOURCE_COUNT } IDH_RTSOURCE;

typedef struct _idh_handle {
    int dummy;
}* idh_handle_t;

typedef struct _idh_source {
    int dummy;
}* idh_source_t;

typedef struct _idh_batch {
    int dummy;
}* idh_batch_t;

typedef struct _idh_tag {
    unsigned char data_type;
    unsigned short namespace_index;
    const char* tag_name;
} idh_tag_t;

typedef struct _idh_real {
    unsigned long long quality : 16;  // IDH_QUALITY
    long long timestamp : 48;         // million second from 1970-01-01 00:00:00
    double value;                     // value
} idh_real_t;

LIBIDH_API idh_handle_t idh_instance_create();

LIBIDH_API void idh_instance_destroy(idh_handle_t handle);

/* data source */

LIBIDH_API idh_source_t idh_source_create(idh_handle_t handle, IDH_RTSOURCE source_type,
                                          const char* source_schema, int sample_timespan_msec,
                                          int support_subscribe);

LIBIDH_API void idh_source_destroy(idh_source_t source_id);

LIBIDH_API int idh_source_readvalues(idh_source_t source_id, idh_real_t* values,
                                     const idh_tag_t* tags_ptr, int tags_size);

LIBIDH_API int idh_source_writevalues(idh_source_t source_id, int* results, const double* values,
                                      const idh_tag_t* tags_ptr, int tags_size);

/* batch operators. speed up for high frequency read/write */

LIBIDH_API idh_batch_t idh_batch_create(idh_source_t handle);

LIBIDH_API int idh_batch_subscribe(idh_batch_t batch_id, int* results, const idh_tag_t* tags_ptr,
                                   unsigned tags_size);

LIBIDH_API void idh_batch_unsubscribe(idh_batch_t batch_id, const idh_tag_t* tags_ptr,
                                      unsigned tags_size);

LIBIDH_API
int idh_batch_readvalues(idh_batch_t batch_id, idh_real_t* values_ptr, const idh_tag_t* tags_ptr,
                         unsigned tags_size);

LIBIDH_API int idh_batch_writevalues(idh_batch_t batch_id, int* results, const double* values_ptr,
                                     const idh_tag_t* tags_ptr, unsigned tags_size);

LIBIDH_API void idh_batch_destroy(idh_batch_t batch_id);

#ifdef __cplusplus
}
#endif
