#!/bin/sh
sudo apt install ffmpeg -y
pip install -r requirements.txt
cd instant-ngp
pip install -r requirements.txt
git clone --recursive https://github.com/cvg/Hierarchical-Localization/
cd Hierarchical-Localization/
python -m pip install -e .
