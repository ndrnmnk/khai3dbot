#!/bin/sh
cd instant-ngp
git clone --recursive https://github.com/cvg/Hierarchical-Localization/
cd Hierarchical-Localization/
python -m pip install -e .
cd ../
sudo apt install ffmpeg
