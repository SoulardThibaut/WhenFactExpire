#!/bin/bash
#SBATCH --gres=gpu:1


# cd ..
python3 -u main.py -d FD_Y_Medium -m TimePlex_base -a '{"embedding_dim":100, "srt_wt":5.0, "ort_wt":5.0, "sot_wt":5.0, "emb_reg_wt":0.005}' -l crossentropy_loss_AllNeg -r 0.1 -b 500 -x -1 -n 0 -v 1 -q 0 -y 10 -g_reg 2 -g 2.0 --perturb_time 1 --mode train --flag_add_reverse 1 -e 100 --save_dir FD_Y_Medium_TimePlex_base --timeout 7200 --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TimePlex_base --resume_from_save "./models/FD_Y_Medium_TimePlex_base/best_valid_model.pt" --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TimePlex_base" --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TimePlex -a '{"embedding_dim":100, "model_path":"./models/FD_Y_Medium_TimePlex_base/best_valid_model.pt", "pairs_wt":3.0, "pairs_args":{"reg_wt":0.002}}' -l crossentropy_loss -r 0.05 -b 500 -x -1 -n 100 -v 1 -q 0 -y 10  -g 1.0 -bt 0 --patience 1 -e 20 --save_dir FD_Y_Medium_TimePlex --timeout 7200 --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TimePlex --resume_from_save "./models/FD_Y_Medium_TimePlex/best_valid_model.pt"  --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TimePlex" -bt 0 --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TComplex_lx -a '{"embedding_dim":100}' -l crossentropy_loss -r 0.05 -b 500 -x -1 -n 100 -v 1 -q 0 -y 10  -g 1.0 --patience 1 -e 100 --save_dir FD_Y_Medium_TComplex_lx --timeout 7200 --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TComplex_lx --resume_from_save "./models/FD_Y_Medium_TComplex_lx/best_valid_model.pt"  --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TComplex_lx" --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TNTComplex_lx -a '{"embedding_dim":100}' -l crossentropy_loss -r 0.05 -b 500 -x -1 -n 100 -v 1 -q 0 -y 10  -g 1.0 --patience 1 -e 100 --save_dir FD_Y_Medium_TNTComplex_lx --timeout 7200 --time_precision "Y"
python3 -u main.py -d FD_Y_Medium -m TNTComplex_lx --resume_from_save "./models/FD_Y_Medium_TNTComplex_lx/best_valid_model.pt"  --mode test --predict_time 1 -y 10 --save_time_results "./Res_server/FD_Y_Medium/TNTComplex_lx" --time_precision "Y"


