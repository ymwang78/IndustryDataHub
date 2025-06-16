import unittest
from pyidh import (
    IDHLibrary,
    IDH_ERRCODE,
    IDH_DATATYPE,
    IDH_QUALITY,
    IDH_RTSOURCE,
    IDH_INVALID_HANDLE,
    idh_source_desc_t,
    idh_tag_t,
    idh_real_t
)

class TestDiscovery(unittest.TestCase):
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
            hostname="localhost",
            port=0
        )
        self.assertGreater(discovery_result, 0, "No UA servers discovered")
        print("\nDiscovered UA Servers:")
        for i in range(discovery_result):
            print(f"Server {i+1}:")
            print(f"  Type: {source_descs[i].source_type}")
            print(f"  Name: {source_descs[i].name.decode('utf-8')}")
            print(f"  Schema: {source_descs[i].schema.decode('utf-8')}")

    def test_da_discovery(self):
        source_descs = [
            idh_source_desc_t(
                source_type=IDH_RTSOURCE.IDH_RTSOURCE_DA.value,
                name=b"",
                schema=b""
            )
            for _ in range(16)
        ]
        discovery_result = self.idh.discovery(
            source_descs,
            hostname="localhost",
            port=0
        )
        self.assertGreater(discovery_result, 0, "No DA servers discovered")
        print("\nDiscovered DA Servers:")
        for i in range(discovery_result):
            print(f"Server {i+1}:")
            print(f"  Type: {source_descs[i].source_type}")
            print(f"  Name: {source_descs[i].name.decode('utf-8')}")
            print(f"  Schema: {source_descs[i].schema.decode('utf-8')}")

if __name__ == '__main__':
    unittest.main() 