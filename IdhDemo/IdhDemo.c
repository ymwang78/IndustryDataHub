// IdhTest.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <idh/libidh.h>

#ifdef _DEBUG
LIBIDH_API void idh_test();
#endif

static void test_source_read(idh_source_t source, idh_tag_t tags[9]) {
    int ret = 0;
    /*source operators*/
    idh_real_t read_values[9];

    ret = idh_source_readvalues(source, read_values, tags, 9);

    for (int i = 0; i < 9; ++i) {
        printf("value: %hu:%s %f\n", tags[i].namespace_index, tags[i].tag_name,
               read_values[i].value);
    }
}

static void test_source_write(idh_source_t source, idh_tag_t tags[9]) {
    int ret = 0;
    /*source operators*/
    int results[9] = {-1, -1, -1, -1, -1, -1, -1, -1, -1};
    double write_values[9] = {rand() * 1.234,
                              -rand() * 1.2,
                              -rand() * rand(),
                              rand() * rand(),
                              -rand(),
                              rand(),
                              12,
                              -34,
                              1};

    ret = idh_source_writevalues(source, results, write_values, tags, 9);

    for (int i = 0; i < 9; ++i) {
        printf("write: %hu:%s %f %d\n", tags[i].namespace_index, tags[i].tag_name, write_values[i],
               results[i]);
    }
}

static void test_batch_subscribe(idh_batch_t batch, idh_tag_t tags[9]) {
    int results[9] = {-1, -1, -1, -1, -1, -1, -1, -1, -1};
    int ret = idh_batch_subscribe(batch, results, tags, 9);
    for (int i = 0; i < 9; ++i) {
        printf("subscribe: %hu:%s %d\n", tags[i].namespace_index, tags[i].tag_name,
               results[i]);
    }
}

static void test_batch_unsubscribe(idh_batch_t batch, idh_tag_t tags[9]) {
    idh_batch_unsubscribe(batch, tags, 9);
}

static void test_batch_readvalues(idh_batch_t batch, idh_tag_t tags[9]) {
    int ret = 0;
    /*source operators*/
    idh_real_t read_values[9];

    ret = idh_batch_readvalues(batch, read_values, tags, 9);

    for (int i = 0; i < 9; ++i) {
        printf("batch read: %hu:%s %f\n", tags[i].namespace_index, tags[i].tag_name,
               read_values[i].value);
    }
}

static void test_batch_writevalues(idh_batch_t batch, idh_tag_t tags[9]) {
    int ret = 0;
    /*source operators*/
    int results[9] = {-1, -1, -1, -1, -1, -1, -1, -1, -1};
    double write_values[9] = {rand() * 1.234,
                              -rand() * 1.2,
                              -rand() * rand(),
                              rand() * rand(),
                              -rand(),
                              rand(),
                              12,
                              -34,
                              1};

    ret = idh_batch_writevalues(batch, results, write_values, tags, 9);

    for (int i = 0; i < 9; ++i) {
        printf("batch write: %hu:%s %f %d\n", tags[i].namespace_index, tags[i].tag_name, write_values[i],
               results[i]);
    }
}

int main() {
    int ret = 0;

    srand(time(NULL));

    idh_tag_t tags[] = {
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.Double"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.Float"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.Int32"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.UInt32"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.Int16"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.UInt16"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.Byte"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.SByte"},
        {IDH_DATATYPE_REAL, 3, "Demo.Static.Scalar.Boolean"},
    };

    idh_handle_t idh = idh_instance_create();

    idh_source_t source =
        idh_source_create(idh, IDH_RTSOURCE_UA, "opc.tcp://172.26.52.54:48010", 1000, 1);

    test_source_read(source, tags);

    test_source_write(source, tags);

    test_source_read(source, tags);

    /*batch operators*/

    idh_batch_t batch = idh_batch_create(source);

    test_batch_subscribe(batch, tags);

    test_batch_readvalues(batch, tags);

    test_batch_writevalues(batch, tags);

    test_batch_readvalues(batch, tags);

    getchar();

    test_batch_unsubscribe(batch, tags);

    idh_batch_destroy(batch);

    idh_source_destroy(source);

    idh_instance_destroy(idh);

}