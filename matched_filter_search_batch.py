import sys
import os
import argparse
sys.path.append(os.getcwd())
import re
import h5py as h5
import numpy as np
import utils
import fast_matched_filter as fmf
from time import time as give_time
import logging
from datetime import datetime

# 解析命令行参数
parser = argparse.ArgumentParser(description='Run matched filter search with customizable parameters.')

parser.add_argument('--threshold', type=float, default=0.25,
                    help='Threshold for event detection (default: 0.25)')
parser.add_argument('--weight_array', nargs='+', type=float, default=[1, 0, 0],
                    help='Weight array for components (default: [1, 0, 0])')
parser.add_argument('--station',type=str, default='Xs28',
                    help='Station to run matched filter')
parser.add_argument('--log_dir',type=str, default='logs_814-918',
                    help='Directory containing log files (default: logs)')
parser.add_argument('--template_dir', type=str, default='./templates/',
                    help='Directory containing template files (default: ./templates/)')
parser.add_argument('--h5_dir', type=str, default='./h5/',
                    help='Directory containing data files (default: .)')
parser.add_argument('--architecture', type=str, default='cpu',
                    choices=['cpu', 'gpu'],
                    help='Architecture to run matched filter (default: cpu)')
parser.add_argument('--is_comp', type=bool, default=False,
                    help='Use dynamic threshold based on std of cc_sum (default: False)')

args = parser.parse_args()

def extract_date_safe(filename):
    try:
        date_str = filename.split('_')[0]
        return datetime.strptime(date_str, '%Y%m%d')
    except (IndexError, ValueError):
        # 如果解析失败，返回一个极大时间，排在最后
        return datetime.max
def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    return 0
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
station = args.station
threshold = args.threshold
log_dir = args.log_dir
weight_str = '_'.join(map(str, args.weight_array))
if not os.path.exists(f'./{log_dir}/{station}'):
    os.makedirs(f'./{log_dir}/{station}')
log_filename = f'./{log_dir}/{station}/{station}_matched_filter_threshold{threshold}_weight{weight_str}_{current_time}.log'

# 配置日志格式和级别
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_filename,
                    filemode='w')
# 创建控制台输出
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

h5_dir = args.h5_dir + station +'/'
template_dir = args.template_dir

sac_events = [f for f in os.listdir(h5_dir) if f.endswith('.h5')]
sac_events.sort(key=extract_date_safe)
template_events = [f for f in os.listdir(template_dir) if f.endswith('.h5')]
template_events.sort(key=extract_number)

logging.info(f'Matched templates: {template_events}')
logging.info(f'Matched sac events: {sac_events}')

threshold = args.threshold
pre_weight_array = np.array(args.weight_array, dtype=np.float32)
logging.info(f'Parameter to run matched filter search: threshold = {threshold}, weight_array = {pre_weight_array}')

result_file = f'./{log_dir}/{station}/{station}_matched_filter_results_threshold{threshold}_weight{weight_str}.h5'


for template_idx, template_event in enumerate(template_events):
    logging.info(f"Processing template {template_event} ({template_idx + 1}/{len(template_events)})")
    try:
        template = utils.load_template(template_event, path=template_dir)
    except Exception as e:
        logging.error(f"Failed to load template '{template_event}': {e}")
        continue

    # 格式化模板输入
    template_array = template['waveforms'][np.newaxis, :]
    moveouts = np.hstack((
        template['moveouts_S'].reshape(-1, 1),
        template['moveouts_S'].reshape(-1, 1),
        template['moveouts_P'].reshape(-1, 1)
    ))
    moveout_array = moveouts[np.newaxis, :]

    # 初始化权重矩阵
    weight_array = np.ones_like(moveout_array, dtype=np.float32)
    n_stations = weight_array.shape[1]
    n_components = weight_array.shape[2]
    weight_array /= np.float32(n_stations * n_components)
    weight_array = pre_weight_array

    matched_filter_step = 1
    architecture = args.architecture

    matched_count = 0
    #global_offset = 0  # 全局样本偏移量
    #current_template_daily = []
    #current_template_all = []
    # 打开 HDF5 文件以检查现有数据
    with h5.File(result_file, 'a') as f:
        if template_event not in f:
            grp = f.create_group(template_event)
            grp.attrs['template_event'] = template_event
        else:
            grp = f[template_event]

        # 检查是否已存在 daily 组
        if 'matched_event_index_daily' not in grp:
            daily_grp = grp.create_group('matched_event_index_daily')
        else:
            daily_grp = grp['matched_event_index_daily']
        existing_dates_per_template = list(daily_grp.keys())  # 获取已处理的日期
        # 遍历 sac_events 并记录索引
        for sac_idx, sac_event in enumerate(sac_events):
            date = str(sac_event.split('_')[0])
            data = utils.load_data(sac_event,path=h5_dir)
            if date in existing_dates_per_template:
                logging.info(f"Template '{template_event}' Day '{date}' data already exists in the result file. Skipping.")
                #这里读取一下global数据
                #matched_indices_local = f[template_event][date]
                #matched_indices_global = [global_offset + idx for idx in matched_indices_local]
                #current_template_all.extend(matched_indices_global)
                #global_offset += data['waveforms'].shape[-1]
                continue
            sampling_rate = data['metadata']['sampling_rate']
            t_start = give_time()
            cc_sum = fmf.matched_filter(template_array,
                                        moveout_array,
                                        weight_array,
                                        data['waveforms'],
                                        matched_filter_step,
                                        arch=architecture)
            t_end = give_time()
            logging.info(f'successfully match template:{template_event} with sac data:{sac_event} , consuming {t_end - t_start:.2f} seconds')
            # 动态或静态阈值判断
            curr_threshold = threshold
            if args.is_comp:
                curr_threshold = 2.5 * np.std(cc_sum[0, :])
                logging.info(f"Using dynamic threshold: {curr_threshold} for sac event {sac_event}")

            matched_event_mask = np.abs(cc_sum[0, :]) > curr_threshold
            matched_indices_local = np.where(matched_event_mask)[0].tolist()
            #matched_indices_global = [global_offset + idx for idx in matched_indices_local]
            #current_template_daily = matched_indices_local
            #global_offset += data['waveforms'].shape[-1]
            #current_template_all.extend(matched_indices_global)
            # 写入 HDF5 文件
            daily_grp = f[template_event]['matched_event_index_daily']
            date_grp = daily_grp.create_group(date)
            date_grp.attrs['date'] = date
            date_grp.create_dataset('matched_event_index', data=np.array(matched_indices_local, dtype=np.int64))

        # 写入 HDF5 文件
        # 存储全局匹配结果
        #all_array = np.array(current_template_all, dtype=np.int64)
        #grp.create_dataset('matched_event_index_all', data=all_array)
        # 计算匹配总数
        for date in daily_grp.keys():
            try:
                matched_indices_local = daily_grp[date]['matched_event_index'][()]
                matched_count += len(matched_indices_local)
            except KeyError:
                logging.warning(f"Failed to read matched indices for date '{date}'. Skipping.")

        # 写入匹配总数
        if 'matched_count' in grp:
            del grp['matched_count']  # 删除旧数据集
        grp.create_dataset('matched_count', data=np.array(matched_count))

    logging.info(f"Finished processing template '{template_event}', matched count: {matched_count}")