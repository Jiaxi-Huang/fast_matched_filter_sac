import sys
import os
import re
import h5py as h5
import numpy as np
import matplotlib.pyplot as plt
from obspy.core import UTCDateTime as udt
# 加载工具函数
import utils
# 定义 output/event 目录的路径
event_dir = './templates/'
output_dir = './templates_spectra/'  # 保存频谱图的目录
os.makedirs(output_dir, exist_ok=True)
data = utils.load_data('./templates_images/20230901_Xs28.h5')



# 提取文件名中的数字部分
def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    return 0

# 绘制模板频谱
def plot_template_spectrum(template_metadata, sampling_rate=250):
    """
    绘制模板波形的频谱图。
    
    参数：
    - template_metadata: 模板元数据，包含波形信息。
    - sampling_rate: 采样率，默认为 250 Hz。
    """
    template_waveforms = template_metadata['waveforms']
    n_stations = template_waveforms.shape[0]
    n_components = template_waveforms.shape[1]
    duration = template_waveforms.shape[2]

    # 频率轴
    freqs = np.fft.rfftfreq(duration, d=1 / sampling_rate)

    # 创建绘图
    figsize = (20, 10)  # 图像大小
    plt.figure('template_spectrum', figsize=figsize)
    for s in range(n_stations):
        for c in range(n_components):
            plt.subplot(n_stations, n_components, s * n_components + c + 1)
            
            # 对波形执行 FFT
            spectrum = np.abs(np.fft.rfft(template_waveforms[s, c, :]))
            
            # 绘制频谱
            plt.plot(freqs, spectrum, lw=0.75, label=f"{data['metadata']['components'][c]}")
            plt.legend(loc='best', frameon=False, handlelength=0.1)
            plt.xlim(0, sampling_rate / 2)  # 显示到奈奎斯特频率
            plt.xlabel('Frequency (Hz)')
            if s == 0 and c ==0:
                plt.ylabel('Amplitude')
            
    # 调整布局
    plt.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.95, hspace=0.3, wspace=0.3)

# 获取目录下所有 .h5 文件
h5_files = [f for f in os.listdir(event_dir) if f.endswith('.h5')]
h5_files = sorted(h5_files, key=extract_number)

# 遍历每个模板文件并生成频谱图
for h5_file in h5_files:
    template = utils.load_template(h5_file, path=event_dir)
    plot_template_spectrum(template, sampling_rate=250)
    # 保存频谱图
    output_path = os.path.join(output_dir, h5_file.split('/')[-1].split('.')[0] + '_spectrum.png')
    plt.savefig(output_path)
    plt.close()

print("Plot Spectrum Done!")