"""Integrated stepper control and image capture module.





"""
import argparse
from time import sleep

import cv2
from serial import Serial, SerialException, SerialTimeoutException


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-t', '--serial-tty', type=str, help='Serial TTY')
parser.add_argument('-c', '--camera-index', type=int, help='Camera ID', default=0)
parser.add_argument('-p', '--path', type=str, help='Image save path', default="./images")
parser.add_argument('-h', '--height', type=int, help='Height of image, in pixels', default=480)
parser.add_argument('-w', '--width', type=int, help='Width of image, in pixels', default=640)
parser.add_argument('-b', '--baud', type=int, help='Baud rate for serial IO', default=9600)
args = parser.parse_args()


def move(serial_device: Serial, steps: int=1, verify: bool=None, step_wait: float=.0015):
    """Moves motor specified steps.

    After sending the movement instruction, optionally verifies controller received the
    instruction and waits 1.5ms (by default) per step taken before returning.

    Arguments:
        serial_device (Serial): Serial device handle.
        steps (int): Number of steps to send to stepper controller. Min: -32768, Max: 32768,
            Default: 1.
        verify (bool): When True, waits for verification from controller.
        step_wait (float): Amount of time, in seconds, to allow the motor to move one step.
            Default: .0015.
    """

    try:
        serial_device.write(steps.to_bytes(2, byteorder='little', signed=True))
    except OverflowError:
        raise ValueError("Steps must in range(-32768, 32768)")

    # Get confirmation from controller of number steps taken
    if verify:
        response = int.from_bytes(serial_device.read(2), byteorder='little', signed=True)
        if steps != response:
            raise ValueError(f"Controller sent an invalid response: {response}")

    # Wait estimated amount of time to make movement, this is controller/motor dependent.
    sleep(step_wait * abs(steps))


def capture(camera: cv2.VideoCapture, path: str=None, session_label: str=None,
            image_label: str=None, display: bool=True):
    """Captures frame from camera, saves to disk with specified session and image labels.

    Filenames will be saved as "image.png", unless the optional session and image labels
    are included. For example, providing a session label of '2017-10-11T21:48:48.288063'
    and an image label of '100' would result in a filename of:

        image_2017-10-11T21:48:48.288063_80.png

    Arguments:
        camera (cv2.VideoCapture): Camera capture instance to obtain image from.
        path (str): Optional path where file should be saved. By default, file will be saved
            within the current directory.
        session_label (str): Optional session label to include in saved image filename.
        image_label (str): Optional image label to include in saved image filename.
        display (bool): When set to False, image will not be displayed upon capture.
            Default: True.
    """

    #todo: work out format
    filename = "{path}image{session_label}{image_label}.png".format(
        path=f"{path}/" if path else "",
        session_label=f"_{session_label}" if session_label else "",
        image_label=f"_{image_label}" if image_label else ""
    )

    print(f"Saving {filename}")

    # Capture, save, and optionally display image
    img = camera.read()[1]
    cv2.imwrite(filename, img)
    if display:
        cv2.imshow('frame', img)
        # Helps primitive UI cycle through events, allegedly
        cv2.waitKey(1)


def setup(serial_tty: str=args.serial_tty, baud: int=args.baud, camera_index: int=args.camera_index,
          height: int=args.height, width: int=args.width, path=args.path):
    """Sets up serial device and camera for use and returns instances of each.

    Arguments:
        serial_tty (str): Path to tty device, e.g. '/dev/tty.usbserial-A8008pzh'.
        baud (int): Baud rate for serial connection. Default: 9600.
        camera_index (int): Index of camera, typically 0 to use default camera.
            Default: 0.
        height (int): Set vertical size of image, in pixels. Default: 480.
        width (int): Set horizontal size of image, in pixels. Default: 640.
        path (str): Optional path where file should be saved. By default, file will be saved
            within the current directory.

    Returns:
        serial_device (Serial), camera (VideoCapture), path (str)
    """
    try:
        serial_device = Serial(serial_tty, baud, timeout=3)
    except SerialException as e:
        raise CaptureError(e)

    try:
        assert b'ready\r\n' == serial_device.readline()
    except (AssertionError, SerialTimeoutException):
        raise CaptureError("Failed to establish communications with serial device")

    camera = cv2.VideoCapture(camera_index)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)

    return serial_device, camera, path


def tear_down(serial_device: Serial, camera: cv2.VideoCapture):
    """Tears down connection to serial device and camera.

    Arguments:
        serial_device (serial): Serial device instance to close.
        camera (cv2.VideoCapture): Camera capture instance to shut down.
    """

    serial_device.close()
    camera.release()


def get_properties(camera):
    """Convenience function to return current camera properties."""
    return dict(
        format=camera.get(cv2.CAP_PROP_FORMAT),
        height=camera.get(cv2.CAP_PROP_FRAME_HEIGHT),
        width=camera.get(cv2.CAP_PROP_FRAME_WIDTH),
        frame_rate=camera.get(cv2.CAP_PROP_FPS),
        brightness=camera.get(cv2.CAP_PROP_BRIGHTNESS),
        contrast=camera.get(cv2.CAP_PROP_CONTRAST),
        saturation=camera.get(cv2.CAP_PROP_SATURATION),
        hue=camera.get(cv2.CAP_PROP_HUE),
        gain=camera.get(cv2.CAP_PROP_GAIN),
        exposure=camera.get(cv2.CAP_PROP_EXPOSURE)
    )


class CaptureError(Exception):
    pass
