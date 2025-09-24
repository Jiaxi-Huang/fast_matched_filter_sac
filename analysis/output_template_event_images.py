import sys
import os
import re
sys.path.append(os.getcwd())

import h5py as h5
import numpy as np
import utils
import matplotlib.pyplot as plt
from obspy.core import UTCDateTime as udt

# 定义 output/event 目录的路径
event_dir = './templates/'
data = utils.load_data('./templates_images/LX.Xs28.h5')
# 使用正则表达式提取数字部分，并将其转换为整数
def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    return 0
def plot_template_event(template_metadata,data):
    template_waveforms = template_metadata['waveforms']
    SR = 250
    n_stations = template_waveforms.shape[0]
    n_components = template_waveforms.shape[1]
    duration = template_waveforms.shape[2]
    start_time = udt("2023-09-09T00:00:00.000000Z")
    end_time = udt("2023-09-10T00:00:00.000000Z")
    time_range_seconds = (end_time - start_time)
    origin_time = template_metadata['origin_time']
    tt_P = template_metadata['p_travel_times']
    tt_S = template_metadata['s_travel_times']
    picks_P = origin_time + np.float64(tt_P)
    picks_S = origin_time + np.float64(tt_S)
    T0 = udt('2023,09,09').timestamp
    # use the sampling rate to convert the times
    picks_P_samples = np.int32((picks_P - T0) * SR)
    picks_S_samples = np.int32((picks_S - T0) * SR)
    P_wave_buffer = np.int32(int(0.000005* time_range_seconds) * SR)
    S_wave_buffer = np.int32(int(0.000005* time_range_seconds) * SR)
    beginning_P_windows = picks_P_samples - P_wave_buffer
    beginning_S_windows = picks_S_samples - S_wave_buffer
    template_waveforms = template_metadata['waveforms']
    reference_time = min(beginning_P_windows.min(), beginning_S_windows.min())
    moveouts_P = beginning_P_windows - reference_time
    moveouts_S = beginning_S_windows - reference_time
    moveouts = np.hstack( (moveouts_S.reshape(-1, 1),
                       moveouts_S.reshape(-1, 1),
                       moveouts_P.reshape(-1, 1)) )
    print(moveouts_P)
    
    # plot the template event
    mv_min = 0.
    mv_max = max(moveouts_P.max(), moveouts_S.max())
    time_min = mv_min
    time_max = (duration + mv_max) / SR # in seconds
    figsize = (50, 20) # note: you can play with figsize to better fit your monitor
    plt.figure('template_event', figsize=figsize)
    for s in range(n_stations):
        for c in range(n_components):
            plt.subplot(n_stations, n_components, s * n_components + c + 1)
            # define time in seconds
            time = np.linspace(moveouts[s, c], moveouts[s, c] + duration, duration) / SR
            plt.plot(time, template_waveforms[s, c, :]/np.abs(template_waveforms[s, c, :]).max(), 
                    lw=0.75, label = '{}.{}'.\
                    format(template_metadata['stations'][s], data['metadata']['components'][c]))
            plt.legend(loc='best', frameon=False, handlelength=0.1)
            plt.xlim(time_min, time_max)
            if s == n_stations - 1:
                plt.xlabel('Time (s)')
            else:
                plt.xticks([])
    plt.subplots_adjust(top=0.955,
            bottom=0.09,
            left=0.085,
            right=0.955,
            hspace=0.2,
            wspace=0.2)

# 获取目录下所有 .h5 文件
h5_files = [f for f in os.listdir(event_dir) if f.endswith('.h5')]
h5_files = sorted(h5_files,key=extract_number)

for h5_file in h5_files:
    template = utils.load_template(h5_file,path=event_dir)
    plot_template_event(template,data)
    plt.savefig(os.path.join("./templates_images",h5_file.split('/')[-1].split('.')[0]+'.png'))
    plt.close()