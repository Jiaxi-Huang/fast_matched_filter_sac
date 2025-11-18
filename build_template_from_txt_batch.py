import sys
import os
sys.path.append(os.getcwd())
from collections import defaultdict
import h5py as h5
import numpy as np
import utils
import math
from obspy.core import UTCDateTime as udt
import matplotlib.pyplot as plt

def read_offsets(txt_file):
    try:
        with open(txt_file, 'r') as f:
            offsets = [int(line.strip()) for line in f if line.strip()]
        return offsets
    except FileNotFoundError:
        print(f"Warning: {txt_file} not found. Skipping this file.")
        return []
    except ValueError:
        print(f"Error: Invalid data in {txt_file}. Ensure all lines are integers.")
        return []
# 定义需要处理的 station 文件夹
stations = [
"Xs01",
"Xs02",
"Xs03",
"Xs04",
"Xs05",
"Xs06",
"Xs07",
"Xs08",
"Xs09",
"Xs10",
"Xs11",
"Xs12",
"Xs13",
"Xs14",
"Xs16",
"Xs17",
"Xs18",
"Xs19",
"Xs20",
"Xs21",
"Xs22",
"Xs23",
"Xs24",
"Xs25",
"Xs26",
"Xs27",
"Xs28",
"Xs29",
"Xs28_old"
]
event_date = '20230909'
txt_dir = './template_txt'
h5_dir = './Analysis/template_h5_data(20Highpass)'
output_template_dir = './templates'
duration = 150
# 定义时间范围
start_time = udt("2023-09-09T00:00:00.000000Z")
end_time = udt("2023-09-10T00:00:00.000000Z")

# 计算时间范围的秒数
time_range_seconds = (end_time - start_time)
for station in stations:
    data_file = f"{event_date}_{station}.h5"
    data = utils.load_data(data_file, path=f'{h5_dir}/{station}/')
    offsets = read_offsets(f'{txt_dir}/{station}.txt')
    for offset in offsets:
        # 选择模板开始时间
        # 计算随机选择的时间
        template_start_time = start_time + (offset / 250)

        # 将随机选择的时间转换为Unix时间戳
        template_start_time = template_start_time.timestamp


        # 假设 template_metadata 已经存在
        template_metadata = {
            'depth': [5.688252],
            'latitude': [44.500587],
            'longitude': [6.6641645],
            'origin_time': template_start_time, 
            'p_travel_times': [0],
            's_travel_times': [0],
            'stations': data['metadata']['stations']
        }

        # use the metadata to extract the waveforms of the template event
        # first, retrieve the origin time
        origin_time = template_metadata['origin_time']
        # this time is a timestamp in seconds
        print('Timestamp in seconds: {:.2f}, human readable date: {}'.\
                format(origin_time, udt(origin_time).strftime('%Y,%m,%d--%H:%M:%S')))

        # second, using the travel times we build the picks
        # for both the P and S waves
        tt_P = template_metadata['p_travel_times']
        tt_S = template_metadata['s_travel_times']

        # the picks, or the phase arrivals, are the sum
        # of the origin time and the travel times
        picks_P = origin_time + np.float64(tt_P)
        picks_S = origin_time + np.float64(tt_S)
        for s in range(len(template_metadata['stations'])):
            print('P pick on station {}: {}'.format(template_metadata['stations'][s],
                                                    udt(picks_P[s]).strftime('%Y,%m,%d--%H:%M:%S')))
            print('S pick on station {}: {}'.format(template_metadata['stations'][s],
                                                    udt(picks_S[s]).strftime('%Y,%m,%d--%H:%M:%S')))
            print('\n')
        # get the timestamp of the the beginning of your data
        # in this example, the data start at 2013,03,17 00:00:00
        T0 = udt('2023,09,09').timestamp
        # we can now define our picks as times relative to T0
        # and expressed in number of samples
        #
        # get the sampling rate:
        SR = 250
        # use the sampling rate to convert the times
        picks_P_samples = np.int32((picks_P - T0) * SR)
        picks_S_samples = np.int32((picks_S - T0) * SR)


        # let say we want to extract 1 second before the P wave
        # and 4 seconds before the S wave
        P_wave_buffer = np.int32(int(0.000005* time_range_seconds) * SR)
        S_wave_buffer = np.int32(int(0.000005* time_range_seconds) * SR)

        # these buffers define the beginning of the windows we want
        # to extract on each station
        beginning_P_windows = picks_P_samples - P_wave_buffer
        beginning_S_windows = picks_S_samples - S_wave_buffer
        print('We now have window start times in samples, relative to the beginning of the data array')
        for s in range(len(template_metadata['stations'])):
            print('P window start time on station {}: {:d} samples'.format(
                template_metadata['stations'][s],
                beginning_P_windows[s]))
            print('S window start time on station {}: {:d} samples'.format(
                template_metadata['stations'][s],
                beginning_S_windows[s]))
            print('\n')
        # extract the waveforms:
        # let say we only want to extract the S wave on the
        # horizontal components, and the P wave on the 
        # vertical components
        # we fix the template duration to 8 seconds
        n_stations = len(template_metadata['stations'])
        n_components = len(data['metadata']['components'])
        print("whole event time range seconds",time_range_seconds)
        template_waveforms = np.zeros((n_stations, n_components, duration),
                                    dtype=np.float32)
        print("template_waveforms shape",template_waveforms.shape)
        for s in range(n_stations):
            for c in range(n_components):
                if c < 2:
                    # the data are organized such that c=0 and c=1 are 
                    # the indexes for components north/south and east/west
                    idx_start = beginning_S_windows[s]
                    idx_end = idx_start + duration
                else:
                    idx_start = beginning_P_windows[s]
                    idx_end = idx_start + duration
                #template_waveforms[s, c, :] = data['waveforms'][s, c, idx_start:idx_end]
                template_waveforms[s, c, :] = data['waveforms'][s, c, offset:offset+duration]
        # we now keep in memory the relative time shifts between each channel,
        # which we call the moveouts
        # the reference time is the earliest start time of the windows
        reference_time = min(beginning_P_windows.min(), beginning_S_windows.min())
        moveouts_P = beginning_P_windows - reference_time
        moveouts_S = beginning_S_windows - reference_time

        moveouts = np.hstack( (moveouts_S.reshape(-1, 1),
                            moveouts_S.reshape(-1, 1),
                            moveouts_P.reshape(-1, 1)) )
        print('The horizontal and vertical component moveouts are:')
        for s in range(len(template_metadata['stations'])):
            print('vertical component moveout on station {}: {:d} samples'.format(
                template_metadata['stations'][s],
                moveouts_P[s]))
            print('horizontal component moveout on station {}: {:d} samples'.format(
                template_metadata['stations'][s],
                moveouts_S[s]))
            print('\n')
        # save the output in an h5 file
        os.makedirs(output_template_dir,exist_ok=True)
        os.makedirs(f'{output_template_dir}/{station}',exist_ok=True)
        template_name = f'{offset}_{station}.h5'
        with h5.File(f'{output_template_dir}/{template_name}', mode='w') as f:
            f.create_dataset('depth', data=template_metadata['depth'])
            f.create_dataset('latitude', data=template_metadata['latitude'])
            f.create_dataset('longitude', data=template_metadata['longitude'])
            f.create_dataset('origin_time', data=template_metadata['origin_time'])
            f.create_dataset('p_travel_times', data=template_metadata['p_travel_times'])
            f.create_dataset('s_travel_times', data=template_metadata['s_travel_times'])
            
            f.create_dataset('moveouts_P', data=moveouts_P, compression='gzip')
            f.create_dataset('moveouts_S', data=moveouts_S, compression='gzip')
            f.create_dataset('sampling_rate', data=data['metadata']['sampling_rate'])
            f.create_dataset('waveforms', data=template_waveforms, compression='gzip')
            #这里一定要注意station的转换，byte_和str
            stations_bytes = [s.encode('utf-8') for s in template_metadata['stations']]
            f.create_dataset('stations', data=stations_bytes)
            print('We have just created a h5 database featuring the following datasets:\n', list(f.keys()))