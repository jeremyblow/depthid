# Depth ID

Multi-axis microscope control and image capture for Laser Interferometer 
Gravitational-Wave Observatory (LIGO) mirror coating analysis.

### Assumptions

[]() | []()
--- | ---
Microcontroller | Arduino Uno
Motor Shield | CNC Shield v3.0, A4988 Driver 
Motors | (3) Nema 17 Stepper Motor, 1.8° step angle
Camera | Point Grey Blackfly GigE models (via Spinnaker) or USB cameras (via OpenCV)
Conda  | v4.6.12
Python | v3.6.8
OpenCV | v3.4.2
Grbl   | v1.1f
Microstep | X, Y, Z: full step (MS0/1/2 Lo/Lo/Lo)

### Setup

1. If motor controller has not been flashed, load Grbl onto Arduino. See `docs/setup_grbl.md` for more information.
2. Install project dependencies using Conda. See `docs/setup_win.md` for more information. 

### Configuration

Create a JSON file containing camera, controller, and job  parameters. The following is an 
example, available within `examples/config_win.json`:

```json
{
  "controller": {
    "interface": "grbl",
    "device_name": "COM4",
    "baud_rate": 115200,
    "motors": [
      ["x", 0.50],
      ["y", 0.50],
      ["z", 0.50]
    ]
  },
  "camera": {
    "interface": "spinnaker",
    "camera_index": 0,
    "height": 1200,
    "width": 1920,
    "pixel_format": "Mono 16",
    "exposure_us": 54725.17013549805,
    "gain_db": 15
  },
  "job": {
    "name": "interactive_session",
    "path": "~/Desktop/data/",
    "mode": "interactive",
    "full_screen": false,
    "save_formats": ["tiff", "raw"],
    "pipeline": [
      {"m": "spinnaker", "f": "capture", "i": "camera", "kw": {"wait_before":  0.0, "wait_after": 0.0}},
      {"m": "spinnaker", "f": "transform_ndarray", "i": 0},
      {"m": "opencv", "f": "gray_to_rgb", "i": 1},
      {"m": "opencv", "f": "histogram", "i": 1, "kw": {"bins": 1000}},
      {"m": "mpl", "f": "plot_histogram_fast", "i": 3, "kw": {"log": "10"}},
      {"m": "ui", "f": "display", "i": 2, "kw": {"panel": "main"}},
      {"m": "ui", "f": "display_menu", "kw": {"panel": "sub1"}},
      {"m": "ui", "f": "display", "i": 4, "kw": {"panel": "sub2"}},
      {"m": "ui", "f": "display_status"}
    ]
  }
}
```

##### Controller

The second parameter for each motor is the motor's microstep. This value should reflect the 
the setting on the hardware controller, which is typically set via jumpers. `1.00` indicates 
a full step. Currently Grbl controllers are supported. 

##### Camera

The `interface` parameter controls which software library should be used to interact with
the camera. Blackfly GigE cameras should use `spinnaker`, other USB cameras may use `OpenCV`.

The camera's `pixel_format` dictates which pixel format the camera should use when 
capturing images.  The camera's onboard FPGA can perform high-speed transformations before 
being processed by the host computer. Depending on the resolution of the camera, the 
performance of the host computer, rate of captures, and the output format desired, it may 
be beneficial to allow the camera to perform an initial transformation. 

Otherwise, it is recommended to select a raw format which matches the bit depth of the 
camera's ADC (e.g. `Bayer RG 12`). 

Additional camera settings are configured on a per-job basis. 

##### Job

Several job examples can be found within the `examples/`directory:

* `config_inline.json` - Demonstrates specifying coordinate sequences directly within job file.
* `config_csv.json` - Demonstrates loading an external CSV file containing coordinates.
* `config_generate.json` - Demonstrates parameter-driven coordinate generation. 

Parameter driven sequence generation is in the format:

    "axis1(start,stop,step),axis2(start,stop,step),axis3(start,stop,step)"

Sequences are nested arithmetic progressions of coordinates, starting at the
specified start value, increasing or decreasing by the step(difference) value
on the given axis, until the next progression would exceed the stop value. 
Sequences are nested in the specified order, allow negative steps, and may 
start at any position on the axis. It is not required to use all three axes; 
you may specify from one to three axes, as desired. Values may be expressed as
integers or floating point numbers. 

Example:

    "x(0,1,1),y(1,6,3),z(0,-1,-1)"

Would result in the following coordinate sequence:

    0,1,0
    0,1,-1
    0,4,0
    0,4,-1
    1,1,0
    1,1,-1
    1,4,0
    1,4,-1
    
To create a z-stack at the current XY, `x(0,0,0),y(0,0,0),z(0,99,1)` may be used.  
    
CSV and inline coordinates are in the format:

    x_pos,y_pos,z_pos
    x_pos,y_pos,z_pos
    
If only moving on a single axis, you may exclude other axes, e.g. `,,1` for CSV and `null,null,1`
for inline coordinates. 

An image will be saved to disk in every format specified in the `save_formats` array, or as specified
in a pipeline `save` directive. Documentation regarding pipelines is pending. 


### Usage

Jobs are initiated from the command line. Be sure your virtual environment is activated
prior to execution. Usage example:

    python main.py --config examples/config_win.json
    
When mode is set to `automatic`, progress will displayed on the terminal or in the UI:

    2.22%, Waypoint 1/45, Time 0:00:02.691880/0:07:33.944381, X0 Y0 Z0
    4.44%, Waypoint 2/45, Time 0:00:09.404582/0:07:31.985596, X0 Y0 Z200
    6.67%, Waypoint 3/45, Time 0:00:16.103426/0:07:30.993264, X0 Y0 Z400
    8.89%, Waypoint 4/45, Time 0:00:22.799437/0:07:30.301831, X0 Y0 Z600
    11.11%, Waypoint 5/45, Time 0:00:29.427541/0:07:29.486895, X0 Y0 Z800
    13.33%, Waypoint 6/45, Time 0:00:55.826761/0:07:29.565381, X0 Y200 Z0
    15.56%, Waypoint 7/45, Time 0:01:02.532876/0:07:29.521698, X0 Y200 Z200
    ...


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

This package was created for the LIGO Optics Working Group, Cal State LA. Depth ID and non-Grbl 
source code is provided without warranty, licensed under GPLv3, and copyright 
Jeremy Blow/Seth Linker. 