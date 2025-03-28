#!/bin/sh

pip install -r requirements.txt
cd instant-ngp
pip install -r requirements.txt
git clone --recursive https://github.com/cvg/Hierarchical-Localization/ hlocalization
cd hlocalization
python -m pip install -e .
cd ..

mkdir temp
mkdir splats
mkdir videos
mkdir htmls
