import os
import h5py as h5
from obspy import read
from obspy.core import UTCDateTime as udt
from obspy.signal.filter import highpass
from datetime import datetime
import numpy as np

def sac_to_h5(sac_filenames,save_same,fmin = None, path='./'):
    if not os.path.exists(path):
        os.makedirs(path)
    sac_EPE = sac_filenames[0]
    sac_EPN = sac_filenames[1]
    sac_EPZ = sac_filenames[2]
    # 读取文件
    stream_EPE = read(sac_EPE, debug_headers=True)
    stream_EPN = read(sac_EPN, debug_headers=True)
    stream_EPZ = read(sac_EPZ, debug_headers=True)
    tr_EPE = stream_EPE[0]
    tr_EPN = stream_EPN[0]
    tr_EPZ = stream_EPZ[0]
    # 初始化数据字典
    stations = []
    components = []
    sampling_rates = []
    start_timestamps = []
    end_timestamps = []
    waveforms = []
    
    # 处理Stream

    stations.append(tr_EPE.stats.station)
    components.append(tr_EPE.stats.channel)
    components.append(tr_EPN.stats.channel)
    components.append(tr_EPZ.stats.channel)
    sampling_rates.append(tr_EPE.stats.sampling_rate)
    start_timestamps.append(tr_EPE.stats.starttime.timestamp)
    end_timestamps.append(tr_EPE.stats.endtime.timestamp)
    
    tr_EPE.data = tr_EPE.data * 10**7
    tr_EPN.data = tr_EPN.data * 10**7
    tr_EPZ.data = tr_EPZ.data * 10**7
    if fmin is not None:
        tr_EPE.data = highpass(tr_EPE.data,fmin,250)
        tr_EPN.data = highpass(tr_EPN.data,fmin,250)
        tr_EPZ.data = highpass(tr_EPZ.data,fmin,250)
    waveforms.append(tr_EPE.data)
    waveforms.append(tr_EPN.data)
    waveforms.append(tr_EPZ.data)
    # 将数据转换为NumPy数组
    stations = np.array(stations, dtype=h5.special_dtype(vlen=str))
    components = np.array(components, dtype=h5.special_dtype(vlen=str))
    sampling_rates = np.array(sampling_rates)
    start_timestamps = np.array(start_timestamps,dtype=np.float64)
    end_timestamps = np.array(end_timestamps,dtype=np.float64)
    waveforms = np.array(waveforms)
    #这里是特殊处理
    waveforms = waveforms.reshape(1, waveforms.shape[0], waveforms.shape[1])
    sampling_rates = np.ceil(sampling_rates)
    # 创建HDF5文件
    with h5.File(path+save_same+'.h5', 'w') as hf:
        hf.create_dataset('stations', data=stations)
        hf.create_dataset('components', data=components)
        hf.create_dataset('sampling_rate', data=sampling_rates)
        hf.create_dataset('start_timestamps', data=start_timestamps)
        hf.create_dataset('end_timestamps', data=end_timestamps)
        hf.create_dataset('waveforms', data=waveforms)
        
def load_data(filename, path='./'):
    data = {}
    with h5.File(path + filename, mode='r') as f:
        data['metadata'] = {}
        data['metadata']['stations'] = f['stations'][()].astype('U').tolist()
        data['metadata']['components'] = f['components'][()].astype('U').tolist()
        data['metadata']['date'] = udt(f['start_timestamps'][()])
        data['metadata']['sampling_rate'] = f['sampling_rate'][()]
        data['waveforms'] = f['waveforms'][()]
    return data

def load_template(filename, path='./'):
    template = {}
    with h5.File(path + filename, mode='r') as f:
        for key in f.keys():
            template[key] = f[key][()]
    return template

def load_cc(filename, path='./output/'):
    with h5.File(path + filename, mode='r') as f:
        cc_sum = f['cc_sum'][()]
    return cc_sum

def load_detections(filename, tid, path='./output/'):
    meta = filename + 'meta.h5'
    wav = filename + 'wav.h5'
    detections = {}
    with h5.File(path + meta, mode='r') as f:
        detections['metadata'] = {}
        for key in f[str(tid)].keys():
            detections['metadata'][key] = f[str(tid)][key][()]
    with h5.File(path + wav, mode='r') as f:
        detections['waveforms'] = f[str(tid)]['waveforms'][()]
    detections['metadata']['stations'] = detections['metadata']['stations'].astype('U')
    detections['metadata']['components'] = detections['metadata']['components'].astype('U')
    return detections

def load_result(filename, path='./'):
    """
    从 HDF5 文件中加载 matched_filter_search_batch.py 生成的匹配结果。

    参数:
        filename (str): 结果文件名（如 'matched_filter_results_threshold0.5_weight0.334_0.334_0.334.h5'）
        path (str): 文件所在目录路径，默认为当前目录 './'

    返回:
        results (dict): 包含所有模板匹配结果的字典，格式如下：
            {
                'template1.h5': {
                    'matched_count': int,
                    'matched_event_index_daily': {
                        'YYYYMMDD': list of indices,
                        ...
                    },
                    'matched_event_index_all': list
                },
                ...
            }
    """
    results = {}
    with h5.File(path + filename, 'r') as f:
        for template_event in f.keys():
            group = f[template_event]
            results[template_event] = {}

            # 加载 matched_count
            if 'matched_count' in group:
                results[template_event]['matched_count'] = group['matched_count'][()]

            # 加载 matched_event_index_daily（每日匹配结果）
            if 'matched_event_index_daily' in group:
                daily_grp = group['matched_event_index_daily']
                daily_dict = {}
                for date in daily_grp.keys():
                    try:
                        daily_dict[date] = daily_grp[date]['matched_event_index'][()].tolist()
                    except KeyError:
                        print(f"Failed to read matched indices for date '{date}' in template '{template_event}'. Skipping.")
                results[template_event]['matched_event_index_daily'] = daily_dict

            # 加载 matched_event_index_all
            if 'matched_event_index_all' in group:
                all_list = group['matched_event_index_all'][()].tolist()
                results[template_event]['matched_event_index_all'] = all_list

    return results

def save_result(results, filepath):
    """
    将匹配结果保存到 HDF5 文件中。

    参数:
        results (dict): 包含所有模板匹配结果的字典，格式如下：
            {
                'template1.h5': {
                    'matched_count': int,
                    'matched_event_index_daily': {
                        'YYYYMMDD': list of indices,
                        ...
                    },
                    'matched_event_index_all': list
                },
                ...
            }
        filepath (str): 目标文件路径（包括文件名和扩展名，如 './logs_814-918_overlap/station1/matched_results.h5'）
    """
    with h5.File(filepath, 'w') as f:
        for template_event, data in results.items():
            # 创建模板组
            group = f.create_group(template_event)

            # 保存 matched_count
            if 'matched_count' in data:
                group.create_dataset('matched_count', data=data['matched_count'])

            # 保存 matched_event_index_daily（每日匹配结果）
            if 'matched_event_index_daily' in data:
                daily_dict = data['matched_event_index_daily']
                daily_grp = group.create_group('matched_event_index_daily')
                for date, indices in daily_dict.items():
                    date_grp = daily_grp.create_group(date)
                    date_grp.attrs['date'] = date
                    date_grp.create_dataset('matched_event_index', data=np.array(indices, dtype=np.int64))

            # 保存 matched_event_index_all
            if 'matched_event_index_all' in data:
                group.create_dataset('matched_event_index_all', data=data['matched_event_index_all'])