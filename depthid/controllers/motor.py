from .exception import ControllerException


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
