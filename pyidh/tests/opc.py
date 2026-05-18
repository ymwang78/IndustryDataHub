from pyidh import IDHLibrary, IDH_DATATYPE, IDH_RTSOURCE
import time

# Create IDH Instance
idh = IDHLibrary()

# Create Data Source
source = idh.create_source(
    source_type=IDH_RTSOURCE.IDH_RTSOURCE_DA.value,
    #source_schema="opc.da://localhost/TaiJi.OPC.Sim",
    #source_schema="opc.da://localhost/TjOPCGateV2.1.0",
    source_schema="opc.da://localhost/TaiJi.OPCGate.1",
    #source_schema="opc.da://localhost/Graybox.Simulator.1",
    sample_timespan_msec=1000,
    source_flag=0
)

i = 0
tags = [{
        "data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value,
        "namespace_index": 0,
        #"tag_name": "MV1"
        #"tag_name": "storage.numeric.reg01"
        "tag_name": "Demo.Tag1"
    }]

max_elapsed = 0
while True:
    start = time.time()
    ret = idh.write_values(source, tags,[i])
    if ret[1] != [0]:
        print(f"Write value failed, error code: {ret[0]}", i)
        break
    result, values= idh.read_values(source, tags)
    for value in values:
        print(f"Quality: {value.quality}, Timestamp: {value.timestamp}, Value: {value.value}")
    i += 1
    end = time.time()
    elapsed = end - start
    #print(f"Elapsed time: {elapsed:.2f} seconds")
    if elapsed > max_elapsed:
        max_elapsed = elapsed
        print(f"New max elapsed time: {max_elapsed:.2f} seconds")
    #if elapsed < 1:
    #    time.sleep(1 - elapsed)     


idh.destroy_source(source)
idh.destroy()