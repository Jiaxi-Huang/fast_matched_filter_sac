#!/bin/bash

params=(
    #"0.7 '1.0 0.0 0.0'"
    #"0.7 '0.0 1.0 0.0'"
    #"0.7 '0.0 0.0 1.0'"
    #"0.8 '1.0 0.0 0.0'"
    #"0.8 '0.0 1.0 0.0'"
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
    "Xs17"
    "Xs18"
    "Xs19"
    #"Xs20"
    #"Xs21"
    #"Xs22"
    #"Xs23"
    #"Xs24"
    #"Xs25"
    #"Xs26"
    #"Xs27"
    #"Xs28"
    #"Xs29"
)
h5_dir="./h5/"
template_dir="./templates/"
log_dir="logs_814-918"
architecture="cpu"
for station in "${stations[@]}"; do 
    for param in "${params[@]}"; do
        # 提取 mode/threshold 和 weight_array
        mode_or_threshold=$(echo "$param" | awk '{print $1}')
        weight_array=$(echo "$param" | sed -e 's/^[^ ]* //; s/'\''//g')

        echo "Running with param: $param"

        # 构建基础命令
        cmd="python matched_filter_search_batch.py \
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
        # 启动后台任务
        (
            timeout 60000 $cmd
        ) &
    done
done
# 等待所有后台任务完成
wait
echo "All experiments completed."
