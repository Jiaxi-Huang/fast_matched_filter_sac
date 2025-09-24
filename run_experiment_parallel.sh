#!/bin/bash

# 设置最大并发数
MAX_JOBS=2

params=(
    #"0.7 '1.0 0.0 0.0'"
    #"0.7 '0.0 1.0 0.0'"
    #"0.7 '0.0 0.0 1.0'"
    "0.8 '1.0 0.0 0.0'"
    "0.8 '0.0 1.0 0.0'"
    "0.8 '0.0 0.0 1.0'"
)

stations=(
    #"Xs01"
    #"Xs02"
    #"Xs03"
    #"Xs04"
    #"Xs05"
    #"Xs06"
    #"Xs07"
    #"Xs08"
    #"Xs09"
    #"Xs10"
    #"Xs11"
    #"Xs12"
    #"Xs13"
    #"Xs14"
    #"Xs16"
    #"Xs17"
    #"Xs18"
    #"Xs19"
    #"Xs20"
    #"Xs21"
    #"Xs22"
    #"Xs23"
    #"Xs24"
    #"Xs25"
    #"Xs26"
    #"Xs27"
    #"Xs28"
    "Xs29"
)

# 定义任务函数
run_task() {
    station=$1
    # 提取 mode/threshold 和 weight_array
    mode_or_threshold=$2
    weight_array=$3

    echo "Running with param: $param for station: $station"

    # 构建基础命令
    cmd="python matched_filter_search_batch.py \
        --weight_array $weight_array \
        --station $station"

    # 判断是否是动态阈值模式
    if [ "$mode_or_threshold" == "dynamic" ]; then
        cmd+=" --is_comp True"
    else
        cmd+=" --threshold $mode_or_threshold"
    fi

    # 执行命令
    $cmd
}

export -f run_task

# 使用 sem 控制并发
for station in "${stations[@]}"; do 
    for param in "${params[@]}"; do
        echo "Running with station:$station param: $param"
        sem -j $MAX_JOBS run_task "$station" "$param"
    done
done

# 等待所有任务完成
sem --wait
echo "All experiments completed."