import os
import h5py
from obspy.signal.filter import highpass
import utils

# 获取当前工作目录下的所有子文件夹
#base_sac_path = './sac_data/'
#output_base_path = './h5/'
base_h5_path = './Analysis/h5/'
output_base_path = './Analysis/h5(20Highpass)/'
fmin = 20
# 定义感兴趣的 station 文件夹
h5_stations = [
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
#"Xs23",
#"Xs24",
#"Xs25",
#"Xs26",
#"Xs27",
"Xs28",
"Xs29",
"Xs28old"
]

# 创建输出目录（如果不存在）
os.makedirs(output_base_path, exist_ok=True)

# 遍历每个 station 文件夹
for sac_station in h5_stations:
    print(f"Processing station: {sac_station}")
    # 构建完整的 station 路径
    station_path = os.path.join(base_h5_path, sac_station)
    # 获取该 station 下的所有 SAC 文件
    h5_files = [f for f in os.listdir(station_path) if f.endswith(('.h5'))]
    # 创建对应的输出路径
    output_station_path = os.path.join(output_base_path, sac_station)
    os.makedirs(output_station_path, exist_ok=True)
    for filename in h5_files:
        output_file_path = os.path.join(output_station_path, filename)
        data = utils.load_data(filename,f'{station_path}/')
        print(data.keys())
        for i in range(3):
            data['waveforms'][0][i] = highpass(data['waveforms'][0][i],fmin,250)
                    # 写入新的 .h5 文件
        with h5py.File(output_file_path, 'w') as hf_output:
            hf_output.create_dataset('stations', data=data['stations'])
            hf_output.create_dataset('components', data=data['components'])
            hf_output.create_dataset('sampling_rate', data=data['sampling_rate'])
            hf_output.create_dataset('start_timestamps', data=data['start_timestamps'])
            hf_output.create_dataset('end_timestamps', data=data['end_timestamps'])
            hf_output.create_dataset('waveforms', data=data['waveforms'])

        print(f"Successfully processed and saved: {output_file_path}")
