# fast_matched_filter_sac (FMFS)

A unoffical branch of **fast_matched_filter(FMF) Specifically designed for processing and analyzing SAC data**. 

Documentation at https://ebeauce.github.io/FMF_documentation/.

<p align="center">
<img src="data/fmf.svg" width=350>
</p><br><br><br><br>

## Required software/hardware
- A C compiler that supports OpenMP (default Mac OS compiler clang does not support OpenMP; gcc can be easily downloaded via homebrew)
- CPU version: either Python (v2.7 or 3.x) or Matlab
- GPU version: Python (v2.7 or 3.x) and a discrete Nvidia graphics card that supports CUDA C with CUDA toolkit installed

## Installation

### From source
A simple make + whichever implementation does the trick. Possible make commands are:<br>
    cd envs
    conda create --name FMF_LX --file FMF_tuto_Python_packages.txt
    conda activate FMF_LX
    cd fast_matched_filter
    make python_cpu
    make python_gpu
    make matlab #(optional)
    python setup.py build_ext
    pip install .

NB: 
- Matlab compiles via mex, which needs to be setup before running. Any compiler can be chosen during the setup of mex, because it will be bypassed by the CC environment variable in the Makefile. Therefore CC must be set to an OpenMP-compatible compiler.
- The matching result differ a litter in different operating systems even different hardware. But **it is guranteed that the result of CPU and GPU are the same on the same machine**. 
- We strongly recommend using the the fmf package in this repository to make sure you can reproduce the results.

## Running
- [ ] Some docs need to be implemented here.
```python
FMF_LX/
├── logs # dir that output matching processing log
    ├── station_name(station that you process)
        ├── matched_filter_results_threshold0.5_weight0.0_1.0_0.0.h5 # running result
        ├── matched_filter_results_threshold0.5_weight0.0_1.0_0.0_timestamp.log #running log
|—— analysis
    ├── station_name
        ├── plots of station
|—— scripts #scripts to running the matching procedure
├── sac_data # sac file you download
    ├── station_name_1
        ├── xxx.sac/xxx.EPE/xxx.EPZ/xxx.EPN
    ├── station_name_2
        ├── xxx.sac/xxx.EPE/xxx.EPZ/xxx.EPN
├── h5_data # h5 file that converted from sac file
    ├── station_name_1
        ├── xxx.h5
    ├── station_name_2
        ├── xxx.h5
├── templates # template file
    ├── xxx.h5
├── build_template_from_catalog_batch.ipynb # 批量生成模板文件
├── matched_filter_search_batch.py # 匹配脚本
├── run_experiment.sh # 运行脚本
├── utils.py # 内置函数
├── analysis_template_event.ipynb # 模板文件解析
├── analysis_result.ipynb # 匹配结果解析
```
