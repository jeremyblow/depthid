import logging
import re
from time import sleep, time

from serial import Serial, SerialException


logger = logging.getLogger("depthid")


class ControllerException(Exception):
    pass


class Controller:

    timeout = 5
    linefeed = '\n'
    est_step_time = 0.04
    est_move_time = 0.06
    pos_pattern = re.compile(r"MPos:(?P<x>[\d.-]+),?(?P<y>[\d.-]+)?,?(?P<z>[\d.-]+)?")

    def __init__(self, device_name: str, baud_rate: int, motors: list):
        """
        Arguments:
            device_name (str): Device name, e.g. '/dev/tty.usbserial-A8008pzh' Mac/Linux, 'COM1' Windows.
            baud_rate (int): Baud rate for serial connection. Default: 9600.
        """
        self.device_name = device_name
        self.baud_rate = baud_rate
        self.serial = None
        self.motors = {axis: Motor(axis, microstep) for axis, microstep in motors}
        self.position = {axis: None for axis in self.motors}

    def connect(self):
        try:
            self.serial = Serial(port=self.device_name, baudrate=self.baud_rate, timeout=self.timeout)
        except SerialException as e:
            raise ControllerException(f"Failed to connect to {self.device_name}, {e}")

    def initialize(self, connect=True):
        """Initializes communication with serial device and returns instance."""

        if connect:
            self.connect()

        message = [self.receive() for _ in range(2)][1]

        try:
            assert 'Grbl' in message
        except AssertionError:
            raise ControllerException(f"Failed to receive init from controller; expected Grbl' in '{message}'")

        self.send("G0")

        try:
            self.wait_for("ok", timeout=3)
        except TimeoutError:
            raise ControllerException(f"Timeout while waiting for controller to acknowledge init command")
        else:
            return self.serial

    def send(self, message, send_linefeed=True):
        linefeed = self.linefeed if send_linefeed else ""
        try:
            self.serial.write(f"{message}{linefeed}".encode())
            self.serial.flush()
        except SerialException as e:
            raise ControllerException(f"Failed to send {message} to controller: {e}")
        else:
            logger.debug(f"Sent {message}")

    def receive(self):
        try:
            message = self.serial.readline()
        except SerialException as e:
            raise ControllerException(f"Failed to receive message from controller: {e}")

        try:
            message = message.decode()
        except UnicodeDecodeError as e:
            raise ControllerException(f"Failed to decode {message} from controller: {e}")
        else:
            message = message.rstrip()
            logger.debug(f"Recv {message}")
        return message

    def move(self, waypoint):
        """Move specified axis to absolute position.

        Commands:
            G0: rapid move, move linearly on all axes
            G2: clockwise arc move
            G3: counter-clockwise arc move
            G53: machine coordinate system
            G90: Switch to absolution positioning mode
            G91: Switch to incremental positioning mode
        """
        cmd = "G90 G53 {}".format(
            " ".join([f"{k.upper()}{v}" for k, v in waypoint.items() if v is not None])
        )
        self.send(cmd)
        self.wait_for("ok")
        return self.wait_waypoint(waypoint)

    def jog(self, axis: str, ms_factor: int):
        """Incremental relative movement on given access.

        Grbl requires feed rate for every jog, set to max-ish 8000.

        Arguments:
            axis (str): x, y, or z (see Motor.allowed_axes)
            ms_factor (int): Microstep size factor, should be positive integer
        """
        steps = self.motors[axis].microstep * ms_factor

        # Calculate expected waypoint
        waypoint = self.update_position()
        waypoint[axis] = f"{float(waypoint[axis]) + steps:.3f}"

        self.send(f"$J=G91{axis.upper()}{steps:.4f}F8000")
        self.wait_for("ok")
        return self.wait_waypoint(waypoint)

    def reset(self):
        self.send(f"\x18")
        self.initialize(connect=False)
        self.receive()

    def home(self):
        # Do individually in case we're underpowered
        for motor in self.motors.values():
            self.move({motor.axis: "0.000"})

    def update_position(self):
        # todo: describe behavior
        self.send("?", send_linefeed=False)
        message = self.receive()
        try:
            m = self.pos_pattern.search(message).groupdict()
        except AttributeError:
            raise ControllerException(f"Unexpected output while determining motor position: {message}")
        else:
            self.position.update(**{k: f"{float(v):.3f}" for k, v in m.items() if v is not None})
        return m

    def wait_for(self, value, timeout=0):
        message = None
        timeout = time() + timeout if timeout else None
        while message != value:
            if timeout and time() >= timeout:
                raise TimeoutError
            message = self.receive()

    def wait_waypoint(self, waypoint):
        pos = self.update_position()
        # todo: fix up float/string handling
        dist = max(abs(float(pos[k]) - float(waypoint[k])) for k in waypoint)
        timeout = dist * self.est_step_time * 2
        start = time()
        while not waypoint.items() <= self.update_position().items():
            if time() > start + timeout:
                raise ControllerException(f"Waypoint timeout {timeout}s to {waypoint}, cur {self.update_position()}")
            # Prevent flooding controller
            sleep(self.est_step_time)
        return dist

    def shutdown(self):
        try:
            self.serial.close()
        except AttributeError:
            # Don't raise exception if serial is unset
            pass

    @property
    def parameters(self):
        return dict(
            device_name=self.device_name,
            baud_rate=self.baud_rate,
            motors=[m.parameters for m in self.motors.values()]
        )

    def __repr__(self):
        return f"{len(self.motors)}-Axis Grbl Motor Controller"


class Motor:

    allowed_microsteps = (
        1.0,
        0.5,
        0.25,
        0.125,
        0.0625
    )
    allowed_axes = ('x', 'y', 'z')

    def __init__(self, axis: str, microstep: float = .25):

        self.axis = axis
        self.microstep = microstep
        self.validate()

    def validate(self):

        try:
            assert self.axis in self.allowed_axes
        except AssertionError:
            raise ControllerException(f"{self.axis} label not in {self.allowed_axes}")

        try:
            assert self.microstep in self.allowed_microsteps
        except AssertionError:
            raise ControllerException(
                f"{self.axis} microstep {self.microstep} not in {self.allowed_microsteps}"
            )

    @property
    def parameters(self):
        return [self.axis, self.microstep]
