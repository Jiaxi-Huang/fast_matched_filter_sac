import os
import logging
from collections import defaultdict
import utils

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("process_sac_data.log"),  # 将日志写入文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

# 获取当前工作目录下的所有子文件夹
#base_sac_path = './sac_data/'
#output_base_path = './h5/'
base_sac_path = '/Volumes/MultiStone/814-918/sac_data/'
output_base_path = '/Volumes/MultiStone/814-918/h5/'
# 定义感兴趣的 station 文件夹
sac_stations = [
#"Xs01",
#"Xs02",
#"Xs03",
#"Xs04",
#"Xs05",
#"Xs06",
#"Xs07",
#"Xs08",
#"Xs09",
#"Xs10",
#"Xs11",
#"Xs12",
#"Xs13",
#"Xs14",
#"Xs16",
#"Xs17",
#"Xs18",
#"Xs19",
#"Xs20",
#"Xs21",
#"Xs22",
"Xs23",
#"Xs24",
#"Xs25",
#"Xs26",
#"Xs27",
#"Xs28",
#"Xs29",
]

# 创建输出目录（如果不存在）
os.makedirs(output_base_path, exist_ok=True)

# 遍历每个 station 文件夹
for sac_station in sac_stations:
    logging.info(f"Processing station: {sac_station}")
    # 构建完整的 station 路径
    station_path = os.path.join(base_sac_path, sac_station)
    if not os.path.exists(station_path):
        logging.error(f"Station path does not exist: {station_path}")
        continue

    # 获取该 station 下的所有 SAC 文件
    try:
        sac_files = [f for f in os.listdir(station_path) if f.endswith(('.EPE', '.EPN', '.EPZ'))]
        logging.info(f"Found {len(sac_files)} SAC files in {station_path}")
    except Exception as e:
        logging.error(f"Error reading SAC files from {station_path}: {e}")
        continue

    date_to_files = defaultdict(list)
    for filename in sac_files:
        file_path = os.path.join(station_path, filename)
        parts = filename.split('.')
        if len(parts) >= 3 and parts[2] == sac_station:  # 确保是当前 station
            event_date = parts[1]  # 提取日期部分，如 "20230909"
            date_to_files[event_date].append(file_path)

    # 处理每个日期下的文件
    for event_date, file_list in date_to_files.items():
        logging.info(f"Processing event date: {event_date} with {len(file_list)} files")
        if len(file_list) % 3 != 0:
            logging.warning(f"Incomplete dataset: {event_date} in {sac_station}")
            continue

        # 加载 SAC 数据（传入文件路径列表和事件名称）
        try:
            output_station_path = output_base_path + sac_station  + '/'
            if not os.path.exists(output_station_path):
                os.makedirs(output_station_path);
            utils.load_sac_data(file_list, f"{event_date}_{sac_station}", path=output_station_path)
            logging.info(f"Successfully loaded SAC data for {event_date}_{sac_station}")
        except Exception as e:
            logging.error(f"Error loading SAC data for {event_date}_{sac_station}: {e}")
            continue

        # 加载生成的数据
        try:
            data_file = f"{event_date}_{sac_station}.h5"
            data = utils.load_data(data_file, path=output_station_path)
            logging.info(f"Successfully loaded HDF5 data: {data_file}")

            # 打印数据信息
            logging.info(f"Elements in data: {list(data.keys())}")
            logging.info(f"Metadata keys: {list(data['metadata'].keys())}")
            logging.info(f"Data station: {data['metadata']['stations']}")
            logging.info(f"Data components: {data['metadata']['components']}")
            logging.info(f"Data sampling_rate: {data['metadata']['sampling_rate']}")
            logging.info(f"Data start_date: {data['metadata']['date']}")
            logging.info(f"Data waveform: {data['waveforms']}")
        except Exception as e:
            logging.error(f"Error loading or processing HDF5 data for {event_date}_{sac_station}: {e}")
            continue

logging.info("Processing completed.")