import unittest
from pyidh import (
    IDHLibrary,
    IDH_DATATYPE,
    IDH_RTSOURCE,
    IDH_ERRCODE,
    idh_source_desc_t
)

class TestDADataSource(unittest.TestCase):
    def setUp(self):
        self.idh = IDHLibrary()
        
    def tearDown(self):
        self.idh.destroy()

    def test_da_source(self):
        source = self.idh.create_source(
            source_type=IDH_RTSOURCE.IDH_RTSOURCE_DA.value,
            source_schema="opc.da://localhost/TaiJi.OPC.Sim",
            sample_timespan_msec=1000,
            support_subscribe=1
        )
        self.assertNotEqual(source, -1, "Failed to create DA source")
        self.assertTrue(self.idh.is_source_valid(source), "DA source is not valid")
        tags = [
            {
                "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
                "namespace_index": 1,
                "tag_name": "MV1"
            },
            {
                "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
                "namespace_index": 1,
                "tag_name": "CV2"
            }
        ]
        group = self.idh.create_group(source, "TestGroup")
        self.assertNotEqual(group, -1, "Failed to create group")
        subscribe_result, handles = self.idh.subscribe_group(group, tags)
        self.assertEqual(subscribe_result, IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value, "Failed to subscribe tags")
        group_read_result, group_values = self.idh.read_group_values(group, handles)
        self.assertEqual(group_read_result, IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value, "Failed to read group values")
        for i, value in enumerate(group_values):
            print(f"DA Tag {i+1}:")
            print(f"  Quality: {value.quality}")
            print(f"  Timestamp: {value.timestamp}")
            print(f"  Value: {value.value}")
        group_write_values = [654.321, 210.987]
        group_write_result, group_write_results = self.idh.write_group_values(group, handles, group_write_values)
        self.assertEqual(group_write_result, IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value, "Failed to write group values")
        self.idh.unsubscribe_group(group, handles)
        self.idh.destroy_group(group)
        self.idh.destroy_source(source)

if __name__ == '__main__':
    unittest.main() 