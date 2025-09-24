import os
import numpy as np
import matplotlib.pyplot as plt
from obspy.core import UTCDateTime as udt
import utils
import gc
from datetime import datetime, timedelta

# 加载结果
threshlolds = ['0.7','0.8']
weights =  [[0,'1.0_0.0_0.0'],[1,'0.0_1.0_0.0'],[2,'0.0_0.0_1.0']]
log_name = '814-918(funhpc)'
stations = [
"Xs01",
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
#"Xs28",
#"Xs29",
]
result_dir = './logs_' + log_name
n_best = 8
tempates_dir = './templates/'
components = ['EPE', 'EPN', 'EPZ']  # 根据你的 SAC 数据调整

def extract_matched_waveforms_from_daily(template_event, n_best, result_dict, h5_file, data_dir='./', station_idx=0):
	"""
	根据 matched_event_index_daily 提取每天的匹配事件波形，并返回带有 station_idx 的 detections 字典。
	
	参数:
		template_events: list of str, 多个模板名称
		result_dict: dict, load_result() 返回的结果字典
		h5_file: list of str, 所有 sac 文件名
		data_dir: str, 原始数据路径
		station_idx: int, 当前绘制使用的台站索引（用于画图时定位台站）

	返回:
		detections: dict, key 为 template_idx，value 为对应模板的波形与元数据
	"""
	detection = {}
	# 加载模板以获取模板持续时间（单位：采样点）
	template = utils.load_template(template_event, path='./templates/')
	template_duration = template['waveforms'].shape[-1]  # 获取模板长度（采样点数）
	sampling_rate = 250  # 假设固定采样率，也可以从模板中读取

	waveforms = []
	origin_times = []
	daily_indices_list = result_dict.get(template_event, {}).get('matched_event_index_daily', [])
	if not daily_indices_list:
		print(f"No matched events found for template {template_event}, skipping.")
		return
	for day_idx, indices_in_day in enumerate(daily_indices_list):
		if not indices_in_day:
			continue  # 跳过没有事件的天
		h5_day_data = h5_file[day_idx]
		data = utils.load_data(h5_day_data, path=data_dir)
		wf = data['waveforms']
		wf_time = data['metadata']['date']
		del data
		gc.collect()
		for idx in indices_in_day:
			start_idx = idx
			end_idx = idx + template_duration
			slice_wf = wf[:, :, start_idx:end_idx]
			waveforms.append(slice_wf)
			origin_time = wf_time + idx / sampling_rate
			origin_times.append(origin_time)
			del slice_wf
			# 防止卡死
			if len(waveforms) == 3*n_best:
				break
		if len(waveforms) == 3*n_best:
			break
	detection = {
		'waveforms': np.array(waveforms),
		'metadata': {
			'origin_times': np.array(origin_times),
		}
	}

	return detection

def plot_n_detections(detection, n_best, template,components, weight = 0, station_idx=0, save_pos = None):
	template_waveforms = template['waveforms'][station_idx, :, :]
	detection_waveforms = detection['waveforms']
	if(detection_waveforms.shape[0] < n_best):
		n_best = detection_waveforms.shape[0]
	template_duration =  len(template['waveforms'][0][0])
	# 如果长度不足 n_best，则保持原样
	detection_waveforms = detection_waveforms[:n_best, :, :,:]
	OT = detection['metadata']['origin_times'][:n_best]
	# 如果长度大于 n_best，则随机选取 n_best 个样本
	if len(detection_waveforms) > n_best:
		indices = np.random.choice(len(detection_waveforms), size=n_best, replace=False)
		detection_waveforms = detection_waveforms[indices, :, :,:]
		OT = OT[indices]
	duration = template['waveforms'].shape[-1]
	# start plotting
	time = np.linspace(0., template_duration, duration)
	figsize = (50, 30)
	plt.figure('detection', figsize=figsize)
	plt.suptitle('Station {}'.format(template['stations'][station_idx].decode('utf-8')))
	n_components = 1
	for c in range(n_components):
		plt.subplot(n_best + 1, n_components, 1 + c)
		plt.title(components[c])
		template_waveforms = (template_waveforms - np.mean(template_waveforms)) / np.std(template_waveforms)
		plt.plot(time, template_waveforms[weight, :], lw=0.75, color='C3', label='Template')
		plt.xlim(time.min(), time.max())
		if c == 2:
			plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., handlelength=0.1)
		for n in range(n_best):
			plt.subplot(n_best + 1, n_components, (1 + n)*n_components + c + 1)
			detection_waveforms[n, : ,weight, :][0] = (detection_waveforms[n, : ,weight, :][0] - np.mean(detection_waveforms[n, : ,weight, :][0])) / np.std(detection_waveforms[n, : ,weight, :][0])
			plt.plot(time, detection_waveforms[n, : ,weight, :][0], lw=0.75, color='C0',
					 label=udt(OT[n])\
							 .strftime('%Y,%m,%d -- %H:%M:%S'))
			plt.xlim(time.min(), time.max())
			if n == n_best - 1:
				plt.xlabel('Time (s)')
	plt.subplots_adjust(top=0.91,
			bottom=0.075,
			left=0.06,
			right=0.885,
			hspace=0.2,
			wspace=0.2)
	plt.savefig(save_pos)
	plt.close()
	  
# sac sort
def extract_date_safe(filename):
	try:
		date_str = filename.split('_')[0]
		return datetime.strptime(date_str, '%Y%m%d')
	except (IndexError, ValueError):
		# 如果解析失败，返回一个极大时间，排在最后
		return datetime.max
	

for station in stations:
	for threshold in threshlolds:
		for weight in weights:
			h5_dir = f'./h5/{station}/'
			h5_file = [f for f in os.listdir(h5_dir) if f.endswith('.h5')]
			h5_file.sort(key=extract_date_safe)
			result_file = f'{station}_matched_filter_results_threshold{threshold}_weight{str(weight[1])}.h5'
			result_dict = utils.load_result(result_file, path=f'{result_dir}/{station}/')
			templates = list(result_dict.keys())
			save_dir = f'./analysis_plots/{log_name}/{station}/{station}_matched_filter_results_threshold{threshold}_weight{str(weight[1])}/'
			# 提取匹配事件波形

			# 对每个模板绘制波形图
			for template_idx,template_event in enumerate(templates):
				#if result_dict[template_event]['matched_count'] > 150000:
				#	print(f"{template_name} too much event. Skipping")
				#	continue
				template_name = template_event.split('.')[0]
				if os.path.exists(save_dir + template_name + '_' + components[weight[0]]+'.png'):
					print(f"File {save_dir + template_name + '_' + components[weight[0]]} already exists. Skipping.")  
				else:
					print(f"Processing template: {template_name}")
					detection = extract_matched_waveforms_from_daily(
						template_event, n_best, result_dict, h5_file,data_dir = h5_dir
					)
					if len(detection['waveforms']) == 0:
						print(f"No detections found for {template_name}, skipping.")
						continue

					template = utils.load_template(template_event, path='./templates/')
					# 绘图
					plot_n_detections(
						detection=detection,
						n_best= n_best,
						template=template,
						components=components,
						weight = weight[0],
						station_idx= 0,
						save_pos = save_dir + template_name + '_' + components[weight[0]]
					)