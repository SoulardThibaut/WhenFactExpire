
# Data Retrieval and Processing

This directory contains all the necessary components to process the raw Wikidata dump (2023 version) and generate the benchmark datasets as described in our paper.

The process involves extracting temporally-qualified facts from the raw data, filtering them based on specific criteria, and transforming them into the structured format required for the benchmark.

## Directory Structure

This folder is organized into three main subdirectories:

* **`Data/`**: This is the input directory for the raw data. Before running any scripts, you must download the dataset from our Zenodo archive and place its contents here.
    > **Action Required**: Download the data from Zenodo ([LINK WILL BE ADDED HERE]) and place the files in this directory.

* **`Queries/`**: This folder stores the queries used by the processing scripts to extract temporal facts and their associated metadata from the Wikidata dump.

* **`ScriptsCreationData/`**: This directory holds the Python scripts that form the data transformation pipeline. These scripts read the raw data from the `Data/` folder, apply the queries, perform preprocessing, generate negative samples, and structure the final output into the various benchmark configurations. For detailed instructions on running these scripts, please consult the `README.md` inside this folder.

