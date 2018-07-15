### Python and OpenCV on MacOS with Homebrew

The below setup procedures assume you already have Xcode command line tools installed. If not, 
execute:

    sudo xcode-select --install
    
Further, it assumed homebrew is installed on your system. If not, please visit [Homebrew](https://brew.sh/)
for installation instructions. 

Install [pyenv](https://github.com/pyenv/pyenv), if not already installed:

```bash
brew install autoconf pkg-config readline pyenv pyenv-virtualenv pyenv-virtualenvwrapper
echo 'if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi' >> ~/.bash_profile
echo 'if which pyenv-virtualenv-init > /dev/null; then eval "$(pyenv virtualenv-init -)"; fi' >> ~/.bash_profile
echo 'pyenv virtualenvwrapper' >> ~/.bash_profile
```

Install Python 3.6.2 and create a Python 3.6.2 based  virtual environment for **depthid**:
```bash
pyenv install 3.6.2
pyenv virtualenv 3.6.2 depthid
pyenv activate depthid
```

Install [OpenCV](https://opencv.org/) and bind it to the virtual environment:

```bash
brew install opencv
ln -s /usr/local/opt/opencv/lib/python3.6/site-packages/cv2.cpython-36m-darwin.so ~/.pyenv/versions/depthid/lib/python3.6/site-packages/cv2.so
```

To confirm your environment, launch `python` and import the `cv2` package as shown below.
```
>>> import cv2
>>> cv2.__version__
'3.3.0'
```

Create and change into a directory for your project(s), e.g.:

    mkdir -p ~/Documents/Projects
    cd ~/Documents/Projects

Clone the **depthid** repo, install dependencies:

    git clone https://github.com/jeremyblow/depthid.git
    cd depthid
    pip install -r requirements.txt

### Python and OpenCV on MacOS with Conda

The following procedure assumes a working [Anaconda](https://www.anaconda.com/download/#macos) 
installation is already set up on your system. 

Create and change into a directory for your project(s), e.g.:

    mkdir -p ~/Documents/Projects
    cd ~/Documents/Projects

Clone the **depthid** repo:

    git clone https://github.com/jeremyblow/depthid.git
    cd depthid
   
Create and activate an environment with the necessary packages 
(Python 3.6.2, OpenCV 3.3.0, pyserial):

    conda env create
    source activate depthid

