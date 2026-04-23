#!/bin/bash
#SBATCH --job-name=cantera
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem-per-cpu=5G
#SBATCH --time=12:00:00

#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=avcopan@uga.edu

eval "$(pixi shell-hook --manifest-path /home/avcopan/proj/cantera-helper)"
python ../run.py
