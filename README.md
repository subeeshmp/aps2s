
# Install

You need to have latest version of `conda` installed. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you don't have `conda`. 
> **Note:** `mamba` can also be used and it is much faster than `conda`. Install [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge) to get `mamba`

Install the dependencies and create the conda environment by running the following command:
```
conda env create -f environment.yml
```
or in case of if you are using `mamba`
```
mamba env create -f environment.yml
```

# Usage

Activate the environment by:
```
conda activate aps2s
```

## Create Bathymetry for MITgcm
```
python aps2s.py make_bathy wrf_geo input_bathy

