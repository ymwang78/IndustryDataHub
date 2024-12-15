// IdhTest.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <idh/libidh.h>

#ifdef _DEBUG

__declspec(dllimport) void idh_test();
#endif

static void test_source_read(idh_source_t source, idh_tag_t tags[9]) {
    int ret = 0;
    /*source operators*/
    idh_real_t read_values[9];

    ret = idh_source_readvalues(source, read_values, tags, 9);

    for (int i = 0; i < 9; ++i) {
        printf("value: %hu:%s value:%f, quality:%hx\n", tags[i].namespace_index, tags[i].tag_name,
               read_values[i].value, read_values[i].quality);
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
        printf("write: %hu:%s %f %x\n", tags[i].namespace_index, tags[i].tag_name, write_values[i],
               results[i]);
    }
}

static void test_batch_subscribe(idh_group_t batch, long long tag_handles[9], idh_tag_t tags[9]) {
    int ret = idh_group_subscribe(batch, tag_handles, tags, 9);
    for (int i = 0; i < 9; ++i) {
        printf("subscribe: %hu:%s handle:%llx\n", tags[i].namespace_index, tags[i].tag_name, tag_handles[i]);
    }
}

static void test_batch_unsubscribe(idh_group_t batch, long long tag_handles[9]) {
    idh_group_unsubscribe(batch, tag_handles, 9);
}

static void test_batch_readvalues(idh_group_t batch, long long tag_handles[9], idh_tag_t tags[9]) {
    int ret = 0;
    /*source operators*/
    idh_real_t read_values[9];

    ret = idh_group_readvalues(batch, read_values, tag_handles, 9);

    for (int i = 0; i < 9; ++i) {
        printf("batch read: %hu:%s value:%f quality:%hx\n", tags[i].namespace_index,
               tags[i].tag_name, read_values[i].value, read_values[i].quality);
    }
}

static void test_batch_writevalues(idh_group_t batch, long long tag_handles[9], idh_tag_t tags[9]) {
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

    ret = idh_group_writevalues(batch, results, write_values, tag_handles, 9);

    for (int i = 0; i < 9; ++i) {
        printf("batch write: %hu:%s %f %x\n", tags[i].namespace_index, tags[i].tag_name,
               write_values[i], results[i]);
    }
}

int main() {
    int ret = 0;

    srand((unsigned)time(NULL));

    idh_handle_t idh = idh_instance_create();

#ifdef _DEBUG
    // idh_test();
#endif

    ret = idh_instance_discovery(idh, NULL, 0, "", 0);

    idh_source_desc_t desc_t[16];
    ret = idh_instance_discovery(idh, desc_t, 16, "localhost", 0);

#if 0
    {
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

        idh_source_t source =
            idh_source_create(idh, IDH_RTSOURCE_UA, "opc.tcp://DESKTOP-S7QB5IR:48010", 1000, 1);

        test_source_read(source, tags);

        test_source_write(source, tags);

        test_source_read(source, tags);

        /*batch operators*/

        idh_group_t batch = idh_group_create(source, "test_group");

        long long tag_handles[9] = {-1, -1, -1, -1, -1, -1, -1, -1, -1};

        test_batch_subscribe(batch, tag_handles, tags);

        test_batch_readvalues(batch, tag_handles, tags);

        test_batch_writevalues(batch, tag_handles, tags);

        test_batch_readvalues(batch, tag_handles, tags);

        getchar();

        test_batch_unsubscribe(batch, tag_handles);

        getchar();

        idh_group_destroy(batch);

        idh_source_destroy(source);
    }
#endif  // opc ua

#if 1

    {
        idh_tag_t tags[] = {
            {IDH_DATATYPE_REAL, 3, "MV1"},
            {IDH_DATATYPE_REAL, 3, "MV2"},
            {IDH_DATATYPE_REAL, 3, "MV3"},
            {IDH_DATATYPE_REAL, 3, "CV1"},
            {IDH_DATATYPE_REAL, 3, "CV2"},
            {IDH_DATATYPE_REAL, 3, "CV3"},
            {IDH_DATATYPE_REAL, 3, "DV3"}, //not exists
            {IDH_DATATYPE_REAL, 3, "DV1"},
            {IDH_DATATYPE_REAL, 3, "DV2"},
        };

        idh_source_t source =
            idh_source_create(idh, IDH_RTSOURCE_DA, "opc.da://localhost/TaiJi.OPC.Sim", 1000, 1);

        test_source_read(source, tags);

        test_source_write(source, tags);

        test_source_read(source, tags);

        /*batch operators*/

        idh_group_t batch = idh_group_create(source, "test_group");

        long long tag_handles[9] = {-1, -1, -1, -1, -1, -1, -1, -1, -1};

        test_batch_subscribe(batch, tag_handles, tags);

        test_batch_readvalues(batch, tag_handles, tags);

        test_batch_writevalues(batch, tag_handles, tags);

        test_batch_readvalues(batch, tag_handles, tags);

        getchar();

        test_batch_unsubscribe(batch, tag_handles);

        getchar();

        idh_group_destroy(batch);

        idh_source_destroy(source);
    }

#endif

    idh_instance_destroy(idh);
}