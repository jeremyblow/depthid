# Depth ID

Multi-axis microscope control and image capture for Laser Interferometer 
Gravitational-Wave Observatory (LIGO) mirror coating analysis.

### Assumptions

[]() | []()
--- | ---
Microcontroller | Arduino Uno
Motor Shield | CNC Shield v3.0, A4988 Driver 
Motors | (3) Nema 17 Stepper Motor, 1.8° step angle
Camera | DCM310 3.2M or equivalent USB camera
Python | v3.6.2
OpenCV | v3.4.1
Grbl | v1.1f
Microstep | X, Y, Z: full step (MS0/1/2 Lo/Lo/Lo)

### Setup

1. Load Grbl onto Arduino. See `docs/setup_grbl.md` for more information.
2. Install Python, OpenCV, and project dependencies using Homebrew or Conda. 
    See `docs/setup_env.md` for more information. 

### Configuration

Create a JSON file containing camera and controller parameters. The following
is an example, available within `examples/config.json`:

    {
      "controller": {
        "device_name": "/dev/cu.usbmodem211",
        "baud_rate": 115200,
        "motors": [
          ["x", 1.00],
          ["y", 1.00],
          ["z", 1.00]
        ]
      },
      "camera": {
        "camera_index": 0,
        "height": 480,
        "width": 640
      }
    }
    
Note: the second parameter for each motor is the motor's microstep.

### Usage

Jobs are also specified in JSON. Several job examples can be found within the `examples/`
directory:

* `job_coordinates.json` - Demonstrates specifying coordinate sequences directly within job file.
* `job_csv.json` - Demonstrates loading an external CSV file containing coordinates.
* `job_generate.json` - Demonstrates parameter-driven coordinate generation. Further 
    information is available under the **Job Format** section. 
    
Jobs are initiated from the command line. Be sure your virtual environment is activated
prior to execution. Usage example:

    python main.py --config examples/config.json --job examples/job_generate_2.json

Progress will displayed on the terminal::

    2.22%, Waypoint 1/45, Time 0:00:02.691880/0:07:33.944381, [0, 0, 0]
    4.44%, Waypoint 2/45, Time 0:00:09.404582/0:07:31.985596, [0, 0, 200]
    6.67%, Waypoint 3/45, Time 0:00:16.103426/0:07:30.993264, [0, 0, 400]
    8.89%, Waypoint 4/45, Time 0:00:22.799437/0:07:30.301831, [0, 0, 600]
    11.11%, Waypoint 5/45, Time 0:00:29.427541/0:07:29.486895, [0, 0, 800]
    13.33%, Waypoint 6/45, Time 0:00:55.826761/0:07:29.565381, [0, 200, 0]
    15.56%, Waypoint 7/45, Time 0:01:02.532876/0:07:29.521698, [0, 200, 200]
    ...
    
### Job Format

Jobs are specified in JSON. For example:

    {
      "name": "something",
      "path": "images/",
      "image_format": "tiff",
      "display": true,
      "wait_before": 0.0,
      "wait_after": 0.0,
      "sequence_parameters": "x(0,1,1),y(1,6,3),z(0,-1,-1)"
    }

Parameter driven sequence generation is in the format:

    "axis1(start,stop,step),axis2(start,stop,step),axis3(start,stop,step)"

Sequences are nested arithmetic progressions of coordinates, starting at the
specified start value, increasing or decreasing by the step(difference) value
on the given axis, until the next progression would exceed the stop value. 
Sequences are nested in the specified order, allow negative steps, and may 
start at any position on the axis. It is not required to use all three axes; 
you may specify from one to four axes, as desired.
Example:

    "x(0,1,1),y(1,6,3),z(0,-1,-1)"

Would result in the following coordinate sequence:

    1,0,0
    1,0,-1
    4,0,0
    4,0,-1
    1,1,0
    1,1,-1
    4,1,0
    4,1,-1
    
CSV and inline coordinates are in the format:

    x_pos,y_pos,z_pos
    x_pos,y_pos,z_pos
    
If only moving on a single axis, you may exclude other axes, e.g. `,,1`. 

### Safety

Be mindful of the number of steps per revolution of your motors, and the impact of microstep
selection on your motor shield. There are no safety limits imposed by Depth ID - it will 
_attempt_ to do anything you ask of it. 

### Sources

* https://github.com/gnea/grbl/wiki/Flashing-Grbl-to-an-Arduino
* https://github.com/gnea/grbl/wiki/Grbl-v1.1-Commands
* http://www.zyltech.com/arduino-cnc-shield-instructions/
* https://reprap.org/wiki/NEMA_17_Stepper_motor
* https://www.ligo.org/

### License

This package was created for the LIGO research lab at Cal State LA. Depth ID and non-Grbl 
source code is provided without warranty, licensed under GPLv3, and copyright 
Jeremy Blow/Seth Linker. 