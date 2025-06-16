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
python3 -u main.py -d FD_Y_Medium -m TimePlex_base --resume_from_save "./models/FD_Y_Medium_TimePlex_base/best_valid_model.pt" --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TimePlex_base" --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TimePlex --resume_from_save "./models/FD_Y_Medium_TimePlex/best_valid_model.pt"  --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TimePlex" -bt 0 --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TComplex_lx --resume_from_save "./models/FD_Y_Medium_TComplex_lx/best_valid_model.pt"  --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TComplex_lx" --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TNTComplex_lx --resume_from_save "./models/FD_Y_Medium_TNTComplex_lx/best_valid_model.pt"  --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TNTComplex_lx" --time_precision "Y"


# Clean up monitoring processes
	kill $VMSTAT_PID
	kill $NVIDIA_MONITOR_PID