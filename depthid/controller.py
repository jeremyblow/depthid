import re
from time import sleep

from serial import Serial, SerialException


class Controller:

    timeout = 5
    linefeed = '\n'
    est_step_time = 0.050
    est_move_time = 0.12
    pos_pattern = re.compile(r"MPos:(?P<x>[\d.-]+),?(?P<y>[\d.-]+)?,?(?P<z>[\d.-]+)?,?(?P<w>[\d.-]+)?")

    def __init__(self, device_name: str, baud_rate: int, motors: list):
        """
        Arguments:
            device_name (str): Device name, e.g. '/dev/tty.usbserial-A8008pzh' (Mac/Linux) or 'COM1' (Windows).
            baud_rate (int): Baud rate for serial connection. Default: 9600.
        """
        self.device_name = device_name
        self.baud_rate = baud_rate
        self.serial = None
        self.motors = {axis: Motor(axis, microstep) for axis, microstep in motors}
        self.positions = {axis: None for axis in self.motors}

    def initialize(self):
        """Initializes communication with serial device and returns instance."""
        try:
            self.serial = Serial(port=self.device_name, baudrate=self.baud_rate, timeout=self.timeout)
        except SerialException as e:
            raise RuntimeError(f"Failed to connect to {self.device_name}: {e}")

        message = [self.receive() for _ in range(2)][1]

        try:
            assert 'Grbl' in message
        except AssertionError:
            raise RuntimeError(f"Failed to receive init string from controller; expected Grbl' in '{message}'")

        self.send("G0")
        self.wait_for("ok")
        print("Initialized controller")
        return self.serial

    def send(self, message, send_linefeed=True):
        linefeed = self.linefeed if send_linefeed else ""
        try:
            self.serial.write(f"{message}{linefeed}".encode())
            self.serial.flush()
        except SerialException as e:
            raise RuntimeError(f"Failed to send {message} to controller: {e}")

    def receive(self):
        try:
            message = self.serial.readline()
        except SerialException as e:
            raise RuntimeError(f"Failed to receive message from controller: {e}")

        try:
            message = message.decode()
        except UnicodeDecodeError as e:
            raise RuntimeError(f"Failed to decode {message} from controller: {e}")
        return message.rstrip()

    def move(self, waypoint: list):
        command = [self.motors[axis].command(position) for axis, position in waypoint if position is not None]
        message = " ".join(c for c in command)
        self.send(message)
        self.wait_for("ok")
        self.update_positions()
        while not dict(waypoint).items() <= self.positions.items():
            # Prevent flooding controller
            sleep(.08)
            self.update_positions()
        return message

    def update_positions(self):
        self.send("?", send_linefeed=False)
        message = self.receive()
        try:
            m = self.pos_pattern.search(message).groupdict()
        except AttributeError:
            raise RuntimeError(f"Unexpected output from controller while determining motor position: {message}")
        else:
            self.positions.update(**{k: float(v) for k, v in m.items() if v is not None})

    def wait_for(self, value):
        message = None
        while message != value:
            message = self.receive()

    def shutdown(self):
        self.serial.close()

    @property
    def parameters(self):
        return dict(
            device_name=self.device_name,
            baud_rate=self.baud_rate,
            motors=[m.parameters for m in self.motors.values()]
        )


class Motor:

    allowed_microsteps = (
        1.0,
        0.5,
        0.25,
        0.125,
        0.0625
    )
    allowed_axes = ('x', 'y', 'z', 'w')

    def __init__(self, axis: str, microstep: float=.25):

        self.axis = axis
        self.microstep = microstep
        self.validate()

    def validate(self):

        try:
            assert self.axis in self.allowed_axes
        except AssertionError:
            raise RuntimeError(f"{self.axis} label not in {self.allowed_axes}")

        try:
            assert self.microstep in self.allowed_microsteps
        except AssertionError:
            raise RuntimeError(f"{self.axis} microstep {self.microstep} not in {self.allowed_microsteps}")

    def command(self, position):
        return f"{self.axis.upper()}{position}"

    @property
    def parameters(self):
        return [self.axis, self.microstep]
