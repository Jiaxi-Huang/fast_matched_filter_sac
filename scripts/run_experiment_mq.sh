#!/bin/bash

params=(
    "0.7 '1.0 0.0 0.0'"
    #"0.7 '0.0 1.0 0.0'"
    #"0.7 '0.0 0.0 1.0'"
    #"0.8 '1.0 0.0 0.0'"
    #"0.8 '0.0 1.0 0.0'"
    #"0.8 '0.0 0.0 1.0'"
)

stations=(
    "Xs01" "Xs02" "Xs03" "Xs04" "Xs05" "Xs06" "Xs07" "Xs08" "Xs09" "Xs10"
    "Xs11" "Xs12" "Xs13" "Xs14" "Xs16" "Xs17" "Xs18" "Xs19" "Xs20" "Xs21"
    "Xs22" "Xs23" "Xs24" "Xs25" "Xs26" "Xs27" "Xs28" "Xs29"
)

h5_dir="./h5(20Highpass)/"
template_dir="./templates/"
log_dir="logs_814-918(funhpc)"
architecture="cpu"

# 定义一个锁文件路径
LOCK_FILE="./station_lock"

# 检查并创建锁文件
if [ ! -f "$LOCK_FILE" ]; then
    touch "$LOCK_FILE"
fi

# 定义一个函数处理单个 station 的任务
process_station() {
    local station=$1
    echo "Processing station: $station"

    for param in "${params[@]}"; do
        # 提取 mode/threshold 和 weight_array
        mode_or_threshold=$(echo "$param" | awk '{print $1}')
        weight_array=$(echo "$param" | sed -e 's/^[^ ]* //; s/'\''//g')

        echo "Running with param: $param"

        # 构建基础命令
        cmd="python matched_filter_search_batch_new.py \
            --weight_array $weight_array\
            --station $station\
            --h5_dir $h5_dir\
            --template_dir $template_dir\
            --log_dir $log_dir\
            --architecture $architecture"

        # 判断是否是动态阈值模式
        if [ "$mode_or_threshold" == "dynamic" ]; then
            cmd+=" --is_comp True"
        else
            cmd+=" --threshold $mode_or_threshold"
        fi

        # 执行任务
        timeout 20000 $cmd
    done
}

# 使用文件锁控制 station 的串行化运行
for station in "${stations[@]}"; do
    # 尝试获取锁
    (
        flock -x 200 || exit 1

        # 处理当前 station 的任务
        process_station "$station"

        # 释放锁
    ) 200>"$LOCK_FILE"
done

echo "All experiments completed."