Bot and a website that make 3D reconstruction of objects from videos.

### Installation

- clone this repository
- create a venv for this project
- run `install-all.sh`
- create a different venv for gsplat (because dependency conflicts) and install gsplat
- create `.env` with following fields: 
  - `TOKEN` - Telegram bot token;
  - `GSPLAT_TRAINER` - path to `gsplat/examples/simple_trainer.py`
  - `GSPLAT_VENV` - path to `gsplat/venv/bin/python`


convert_to_splat.py and base.html are modified versions of ones from [this project](https://github.com/antimatter15/splat)