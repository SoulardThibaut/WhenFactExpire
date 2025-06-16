# Temporal Knowledge Graph Embeddings for Validation (TKBI)

## Overview

This directory contains the source code for several Temporal Knowledge Graph Embedding (TKGE) models, adapted from the original [tkbi repository](https://github.com/dair-iitd/tkbi). The code has been specifically modified to perform the **temporal fact validation task** central to our benchmark, rather than the original link prediction task.

## Supported Models

This modified implementation supports the following TKGE models:

* TimePlex_base
* TimePlex
* TComplex
* TNTComplex

## How to Run

1.  **Scripts**: The scripts required to train and evaluate the models are located in the `Scripts_server/` directory. You can configure and launch experiments from here.
2.  **Results**: All evaluation results, logs, and model checkpoints will be saved to the `Res_server/` directory upon completion of the scripts.
3.  **Visualization**: The script to visualize preliminary results can be found in the folder Visualisaiton_local. 
