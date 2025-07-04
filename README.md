# fast_matched_filter_sac (FMFS)

A unoffical branch of **fast_matched_filter(FMF) Specifically designed for processing and analyzing SAC data**. 

Documentation at https://ebeauce.github.io/FMF_documentation/.

<p align="center">
<img src="data/fmf.svg" width=350>
</p><br><br><br><br>


If you use FMF in research to be published, please reference the following article: Beaucé, Eric, W. B. Frank, and Alexey Romanenko (2017). Fast matched-filter (FMF): an efficient seismic matched-filter search for both CPU and GPU architectures. _Seismological Research Letters_, doi: [10.1785/0220170181](https://doi.org/10.1785/0220170181)

FMF is available at https://github.com/beridel/fast_matched_filter and can be downloaded with:<br>

    git clone https://github.com/beridel/fast_matched_filter.git

## Required software/hardware
- A C compiler that supports OpenMP (default Mac OS compiler clang does not support OpenMP; gcc can be easily downloaded via homebrew)
- CPU version: either Python (v2.7 or 3.x) or Matlab
- GPU version: Python (v2.7 or 3.x) and a discrete Nvidia graphics card that supports CUDA C with CUDA toolkit installed

## Installation

### From source
A simple make + whichever implementation does the trick. Possible make commands are:<br>

    make python_cpu
    make python_gpu
    make matlab

NB: Matlab compiles via mex, which needs to be setup before running. Any compiler can be chosen during the setup of mex, because it will be bypassed by the CC environment variable in the Makefile. Therefore CC must be set to an OpenMP-compatible compiler.


### Using pip

Installation as a Python module is possible via pip (which supports clean uninstalling):<br>

    python setup.py build_ext
    pip install .

or simply:<br>

    pip install git+https://github.com/beridel/fast_matched_filter

## Running

Python: Both CPU and GPU versions are called with the matched_filter function.<br>
If FMF was installed with pip:
```python
    import fast_matched_filter as fmf
```

Matlab: The CPU version is called with the fast_matched_filter function

## To do:

- [ ] Update Matlab wrapper.
- [ ] Implement all the new options for GPUs.
