# Windows Setup

The following procedure assumes a clean Windows 10 64-bit installation. Unless otherwise stated, 
accept the default values for any installer questions. 

1. Download and run 
    [Anaconda 2019.03 for Windows Installer](https://repo.anaconda.com/archive/Anaconda3-2019.03-Windows-x86_64.exe).
2. Download and run 
    [Spinnaker 1.20.0.15 Web Installer - Windows (64-bit)](https://www.ptgrey.com/support/downloads/11205/). 
    Note: you may need to register for a Point Grey account.
3. Download and unzip
    [Pyspin](https://www.ptgrey.com/support/downloads/11211/)
    Copy file `spinnaker_python-1.20.0.15-cp36-cp36m-win_amd64.whl` into depthid directory.
4. Ensure your Ethernet network interface is configured to allow jumbo packets (9014 bytes). 
5. Open Anaconda Prompt via Start -> Anaconda3 -> Anaconda Prompt.
6. Change directories into project directory (e.g. `cd Documents\Projects\depthid`).
7. Create virtual environment `conda env create`.
8. Activate virtual environment `activate depthid`
9. Install Pyspin `python -m pip install spinnaker_python-1.20.0.15-cp36-cp36m-win_amd64.whl`

Addendum: 

0. conda update -n base -c defaults conda
1. If MKL dll errors, run `conda update python` while in the virtual env. 
