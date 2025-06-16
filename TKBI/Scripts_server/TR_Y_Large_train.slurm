#!/bin/bash
#SBATCH --gres=gpu:1


# cd ..
mkdir ./Monitoring/$(date +%s)

# Define log files
CPU_LOG="./Monitoring/$(date +%s)/cpu.log"
GPU_LOG="./Monitoring/$(date +%s)/gpu.log"

# Start CPU/RAM monitoring (1-second interval)
vmstat 1 > $CPU_LOG &
VMSTAT_PID=$!
			
# Start GPU monitoring (1-second interval)
while true; do nvidia-smi --query-gpu=name,timestamp,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv >> $GPU_LOG; sleep 25; done &
NVIDIA_MONITOR_PID=$!
python3 -u main.py -d TR_Y_Large -m TimePlex_base -a '{"embedding_dim":100, "srt_wt":5.0, "ort_wt":5.0, "sot_wt":5.0, "emb_reg_wt":0.005}' -l crossentropy_loss_AllNeg -r 0.1 -b 500 -x -1 -n 0 -v 1 -q 0 -y 10 -g_reg 2 -g 2.0 --perturb_time 1 --mode train --flag_add_reverse 1 -e 100 --save_dir TR_Y_Large_TimePlex_base --timeout 7200 --time_precision "Y" 
python3 -u main.py -d TR_Y_Large -m TimePlex -a '{"embedding_dim":100, "model_path":"./models/TR_Y_Large_TimePlex_base/best_valid_model.pt", "pairs_wt":3.0, "pairs_args":{"reg_wt":0.002}}' -l crossentropy_loss -r 0.05 -b 500 -x -1 -n 100 -v 1 -q 0 -y 10  -g 1.0 -bt 0 --patience 1 -e 20 --save_dir TR_Y_Large_TimePlex --timeout 7200 --time_precision "Y"
python3 -u main.py -d TR_Y_Large -m TComplex_lx -a '{"embedding_dim":100}' -l crossentropy_loss -r 0.05 -b 500 -x -1 -n 100 -v 1 -q 0 -y 10  -g 1.0 --patience 1 -e 100 --save_dir TR_Y_Large_TComplex_lx --timeout 7200 --time_precision "Y"
python3 -u main.py -d TR_Y_Large -m TNTComplex_lx -a '{"embedding_dim":100}' -l crossentropy_loss -r 0.05 -b 500 -x -1 -n 100 -v 1 -q 0 -y 10  -g 1.0 --patience 1 -e 100 --save_dir TR_Y_Large_TNTComplex_lx --timeout 7200 --time_precision "Y"


# Clean up monitoring processes
kill $VMSTAT_PID
kill $NVIDIA_MONITOR_PID