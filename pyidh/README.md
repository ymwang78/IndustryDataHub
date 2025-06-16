# PyIDH

Python wrapper for IDH (Industrial Data Hub) library.

## Installation

1. Install Microsoft Visual C++ 2015-2022 Redistributable:
   - 64-bit system: [Download VC140 x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - 32-bit system: [Download VC140 x86](https://aka.ms/vs/17/release/vc_redist.x86.exe)

2. Install pyidh:
```bash
pip install pyidh
```

## Usage

```python
from pyidh import IDHLibrary, IDH_DATATYPE, IDH_RTSOURCE

# Create IDH Instance
idh = IDHLibrary()

# Create Data Source
source = idh.create_source(
    source_type=IDH_RTSOURCE.IDH_RTSOURCE_UA.value,
    source_schema="opc.tcp://localhost:4840",
    sample_timespan_msec=1000,
    support_subscribe=1
)

# Read data
tags = [
    {
        "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
        "namespace_index": 3,
        "tag_name": "Demo.Dynamic.Scalar.Float"
    }
]

result, values = idh.read_values(source, tags)
for value in values:
    print(f"Quality: {value.quality}, Timestamp: {value.timestamp}, Value: {value.value}")

# cleanup
idh.destroy_source(source)
idh.destroy()
```

## Requirements

- Python 3.8 or higher
- Windows operating system
- libidh.dll (included in the package)

## License

MIT License 