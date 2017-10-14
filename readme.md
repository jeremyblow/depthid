# Depth ID

Integrated Arduino stepper control and OpenCV image capture package.

### Usage Example

In this example we will be creating a script which moves the camera 3 steps forward 100 times, 
capturing an image after each movement. After this is complete, we will reset the camera back
to its original position. If you intend on following along with your own equipment, please be
sure to set your environment up as indicated in the **Setup & Requirements** section at the
end of this document. 

To get started, create a Python script with your movement/image capture procedure. For this example,
we'll call the script `session_1.py`. First, inside `session_.1py`, import any necessary functions
from the depthid package:

```python
from depthid import capture, move, setup, tear_down
```

Next, create a function for your procedure. The first step in this function should be to set up
the serial communications with the Arduino, establish a capture session with the camera, and
finally obtain the path where we'll store these images. The parameters for how these things
are set up are declared via the command line, which we'll show later. 

```python
def example_session():
    
    # Setup serial_device and camera for use, obtain path to save images to
    serial_device, camera, path = setup()
```
        
Next, adding to the `example_session` function, let's move the camera and capture some images. 
For this, we'll move the stepper motor 3 steps forward 100 times, taking a picture after 
each movement, then reset the camera back to its original position by moving -300 steps:

```python
    for count in range(1, 101):
        move(serial_device=serial_device, steps=3)
        capture(camera=camera, path=path, session_label="test1", image_label=str(count * 3))
    move(sd=serial_device, steps=-300)
```

The `session_label` and `image_label` allow the image filenames to be saved with dynamic values. 
E.g. `image_test1_80.png`.
        
Finally, release any locks on the devices by calling `tear_down`:

```python
    tear_down(serial_device=serial_device, camera=camera)
```
        
Putting this all together:

```python
from depthid import capture, move, setup, tear_down


def example_session():
    
    # Setup serial_device and camera for use, obtain path to save images
    serial_device, camera, path = setup()
    
    # Move the camera and take pictures. Reset position when done.
    for count in range(1, 101):
        move(serial_device=serial_device, steps=3)
        capture(camera=camera, path=path, session_label="test1", image_label=str(count * 3))
    move(sd=serial_device, steps=-300)
    
    # Wrap things up
    tear_down(serial_device=serial_device, camera=camera)


if __name__ == "__main__":

    example_session()
```


Save this file. To execute your script, call it from the command line. Certain necessary and
optional parameters are passed to the script when called on the command line. The syntax is: 

```bash
python script.py -t <usb tty device> [-p save_path] [-c camera_id] [-h height] [-w width] [-b baud]
```

A most basic example only requires the path to the serial device to be specified:

```bash
python session_1.py -t /dev/tty.usbmodem142311
```
    
If you're on a Mac or Linux, and are uncertain of the path of your USB serial device, you can 
run `ls /dev/tty.*` to see what's available. 

By default, all images will be saved at 640x480 resolution in a subdirectory called `images`.
Below is a more complete example showing further customization:

```bash
python session_1.py -t /dev/tty.usbmodem142311 -p ./images_dir -c 0 -h 1024 -w 1080 -b 9600
```

A more complete usage example can be found in `example.py`. To understand what's going on
underneath the hood, the main package functions are in `depthid/depthid.py` 
    
### Setup & Requirements

To use this package, you will need the following:

* An Arduino compatible microcontroller with appropriate bipolar stepper motor control
* A USB camera (see **Cameras** section below)
* A Mac or Linux computer with:
    * OpenCV 3.3.0 or newer
    * Python 3.6.2 or newer and package dependencies
    * Arduino IDE

Using the Arduino IDE, upload the included INO file found in `arduino/Turbo_the_Camera` to 
your Arduino. 

To install the Python package dependencies, it is recommended you first create a VirtualEnv. Once 
inside your VirtualEnv. you can install the required dependencies via 
`pip install -r requirements.txt`. Naturally, you will execute your script from inside a VirtualEnv. 


### Cameras

Below are cameras which have been or are being tested. However, a wide number of consumer, 
scientific, and industrial cameras will probably work just fine.

* **rocksoul WK-107219SB** (a.k.a. Turbo)
    * Sensor: CMOS
    * Video Modes: 1920x1080, 640x480
    * Max Resolution 5MP video/picture
    * Interface: USB 2.0
* **DCM310 3.2M** (lab microscope cam)
    * Sensor: 1/2 inch, Enhanced COLOR CMOS
    * Max Resolution: 2048*1536
    * Frame Rates: 11 FPS at 2048x1536, 50 FPS at 512x384
    * Video Modes: 2048x1536, 1024x768, 640x480, 512x384
    * Interface: USB 2.0


### License

This package was created for the LIGO research lab at Cal State LA. Source code is provided without
warranty, licensed under GPLv3, and copyright Jeremy Blow. Arduino source code is provided
without warranty, licensed under GPLv3, and copyright Jeremy Blow/Seth Linker. 