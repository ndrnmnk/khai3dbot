#!/bin/sh
sudo apt-get install cmake ninja-build build-essential libboost-program-options-dev libboost-filesystem-dev libboost-graph-dev libboost-system-dev libeigen3-dev libflann-dev libfreeimage-dev libmetis-dev libgoogle-glog-dev libgtest-dev libsqlite3-dev libglew-dev qtbase5-dev libqt5opengl5-dev libcgal-dev libceres-dev nvidia-cuda-toolkit nvidia-cuda-toolkit-gcc gcc-10 g++-10 ffmpeg -y

git clone https://github.com/colmap/colmap.git
export CC=/usr/bin/gcc-10
export CXX=/usr/bin/g++-10
export CUDAHOSTCXX=/usr/bin/g++-10
cd colmap
mkdir build
cd build
cmake .. -GNinja
ninja
sudo ninja install
cd ../..

pip install -r requirements.txt
cd instant-ngp
pip install -r requirements.txt
git clone --recursive https://github.com/cvg/Hierarchical-Localization/
cd Hierarchical-Localization/
python -m pip install -e .
cd ..
mv instant_ngp_utils.py Hierarchical-Localization/hloc/instant_ngp_utils.py
