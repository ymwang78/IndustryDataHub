import unittest
from pyidh import (
    IDHLibrary,
    IDH_DATATYPE,
    IDH_RTSOURCE,
    IDH_ERRCODE,
    idh_source_desc_t
)

class TestUADataSource(unittest.TestCase):
    def setUp(self):
        self.idh = IDHLibrary()
        
    def tearDown(self):
        self.idh.destroy()

    def test_ua_discovery(self):
        source_descs = [
            idh_source_desc_t(
                source_type=IDH_RTSOURCE.IDH_RTSOURCE_UA.value,
                name=b"",
                schema=b""
            )
            for _ in range(16)
        ]
        discovery_result = self.idh.discovery(
            source_descs,
            hostname="192.168.200.105",
            port=48010
        )
        self.assertGreater(discovery_result, 0, "No UA servers discovered")
        print("\nDiscovered UA Servers:")
        for i in range(discovery_result):
            print(f"Server {i+1}:")
            print(f"  Type: {source_descs[i].source_type}")
            print(f"  Name: {source_descs[i].name.decode('utf-8')}")
            print(f"  Schema: {source_descs[i].schema.decode('utf-8')}")

    def test_ua_source(self):
        source = self.idh.create_source(
            source_type=IDH_RTSOURCE.IDH_RTSOURCE_UA.value,
            source_schema="opc.tcp://192.168.200.105:48010/",
            sample_timespan_msec=1000,
            source_flag=2
        )
        self.assertNotEqual(source, -1, "Failed to create UA source")
        self.assertTrue(self.idh.is_source_valid(source), "UA source is not valid")
        tags = [
            {
                "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
                "namespace_index": 3,
                "tag_name": "Demo.Static.Scalar.Double"
            },
            {
                "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
                "namespace_index": 3,
                "tag_name": "Demo.Static.Scalar.Float"
            }
        ]
        result, values = self.idh.read_values(source, tags)
        self.assertGreaterEqual(result, IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value, "Failed to read UA values")
        for i, value in enumerate(values):
            print(f"UA Tag {i+1}:")
            print(f"  Quality: {value.quality} {value.get_quality_high()} {value.get_quality_low()}")
            print(f"  Timestamp: {hex(value.time_quality)} {hex(value.get_timestamp())} {value.get_timestamp_desc()}")
            print(f"  Value: {value.value}")
        write_values = [123.456, 789.012]
        write_result, results = self.idh.write_values(source, tags, write_values)
        self.assertGreaterEqual(write_result, IDH_ERRCODE.IDH_ERRCODE_SUCCESS.value, "Failed to write UA values")
        self.idh.destroy_source(source)

if __name__ == '__main__':
    unittest.main() 