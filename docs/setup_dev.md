```bash
# venv
conda create --name depthid python=3.7.3
conda activate depthid

# big deps (allow versions to roll fwd)
conda install --name depthid numpy opencv pyserial

# write new deps yml
conda env export --no-builds -f environment.yml

# test
python main.py --config examples/config_win.json --job examples/job_interactive.json
```
