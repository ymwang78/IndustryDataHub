import time
from pyidh import (
    IDHLibrary,
    IDH_INVALID_HANDLE,
    IDH_RTSOURCE,
    IDH_DATATYPE,
)

def main():
    # 1. 创建 IDH 实例
    idh = IDHLibrary()

    # 2. 连接 OPC UA 服务器
    opcua_url = "opc.tcp://1.95.140.236:46011"
    source = idh.create_source(
        source_type=IDH_RTSOURCE.IDH_RTSOURCE_UA.value,  # OPC UA
        source_schema=opcua_url,
        sample_timespan_msec=1000,
        support_subscribe=1
    )
    if source == IDH_INVALID_HANDLE:
        print("创建 OPC UA source 失败.")
        return
    if not idh.is_source_valid(source):
        print("OPC UA source 无效.")
        return

    # 3. 配置要采集的标签（点名需根据你的服务器填写）
    tags = [
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 2, "tag_name": "Demo.Count1"},
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 2, "tag_name": "Demo.Count2"},
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 2, "tag_name": "Demo.Count3"},
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 2, "tag_name": "Demo.Count4"},
    ]
    
    write_tags = [
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 2, "tag_name": "Demo.Tag1"},
        {"data_type": IDH_DATATYPE.IDH_DATATYPE_REAL.value, "namespace_index": 2, "tag_name": "Demo.Tag2"},
    ]

    # 4. 读取标签值
    print("=== 单次读取 ===")
    read_result, values = idh.read_values(source, tags)
    for idx, value in enumerate(values):
        print(f"Tag: {tags[idx]['tag_name']}, Quality: {value.quality}, Timestamp: {value.timestamp}, Value: {value.value}")

    # 5. 写入标签值（如服务器支持写入）
    print("=== 写入演示 ===")
    write_values = [123.456, 789.012]
    write_result, results = idh.write_values(source, write_tags, write_values)
    print(f"Write Result: {write_result}, Write Results: {results}")

    # 6. 批量订阅（Group）
    print("=== 批量订阅（Group） ===")
    group_read = idh.create_group(source, "DemoReadGroup")
    print(f"Group Read Handle: {group_read}")
    if group_read == IDH_INVALID_HANDLE:
        print("Group 创建失败")
        return
    read_subscribe_result, read_handles = idh.subscribe_group(group_read, tags)
    print(f"Read Subscribe Result: {read_subscribe_result}, Handles: {read_handles}")
    
    group_write = idh.create_group(source, "DemoWriteGroup")
    print(f"Group Write Handle: {group_write}")
    if group_write == IDH_INVALID_HANDLE:
        print("Group 创建失败")
        return
    write_subscribe_result, write_handles = idh.subscribe_group(group_write, write_tags)
    print(f"Write Subscribe Result: {write_subscribe_result}, Handles: {write_handles}")

    
    # 连续读取 group（订阅/轮询）
    try:
        for _ in range(60):
            group_read_result, group_values = idh.read_group_values(group_read, read_handles)
            for idx, value in enumerate(group_values):
                print(f"[Group] Tag: {tags[idx]['tag_name']}, Value: {value.value}, Quality: {value.quality}, Timestamp: {value.timestamp}")
            
            write_values = [time.time() % 60, time.time() % 60 + 1]  # 模拟写入当前时间的秒数
            group_write_result, group_write_values = idh.write_group_values(group_write, write_handles, write_values)
            print(f"Group Write Result: {group_write_result}, Write Results: {group_write_values}")
            time.sleep(1)
    finally:
        idh.unsubscribe_group(group_read, read_handles)
        idh.destroy_group(group_read)
        idh.unsubscribe_group(group_write, write_handles)
        idh.destroy_group(group_write)

    # 7. 资源释放
    idh.destroy_source(source)
    idh.destroy()
    print("=== 资源清理完毕 ===")

if __name__ == "__main__":
    main()
