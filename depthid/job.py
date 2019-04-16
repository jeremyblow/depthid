import errno
import json
import logging
import os
from datetime import datetime, timedelta
from time import sleep, time

from depthid.camera import Camera, CameraException
from depthid.controller import Controller, ControllerException
from depthid.sequence import Sequence
from depthid.util import get_key, log_dict, pathify, to_csv


logger = logging.getLogger("depthid")


class JobException(Exception):
    pass


class Job:

    def __init__(self, name: str, path: str, controller: Controller, camera: Camera, csv_filename: str = None,
                 sequence_parameters: str = None, coordinates: list = None, mode: str = "automatic", \
                 wait_before: float = 0.0, wait_after: float = 0.0):

        self.start_time = datetime.now()
        self.name = f"{name}_{self.start_time.isoformat().replace(':', '')}"
        self.mode = mode
        self.path = pathify(path)
        self.image_directory = f"{self.path}/{self.name}"
        self.wait_before = wait_before
        self.wait_after = wait_after
        self.controller = controller
        self.camera = camera

        # Statistics
        self.image_times = []
        self.move_times = []

        if csv_filename:
            self.sequence = Sequence.load_csv(csv_filename)
        elif sequence_parameters:
            self.sequence = Sequence.generate(sequence_parameters)
        elif coordinates:
            self.sequence = Sequence.from_coordinates(coordinates)
        elif self.is_interactive:
            self.sequence = Sequence()
        else:
            raise JobException("Either CSV filename, sequence, coordinates, or interactive mode must be provided")

        if self.sequence:
            logger.info(f"Defined {len(self.sequence)} waypoints")

    @classmethod
    def load(cls, job_fh, controller: Controller, camera: Camera):
        with job_fh as fh:
            kwargs = json.load(fh)
        return cls(
            controller=controller,
            camera=camera,
            **kwargs
        )

    def initialize(self):
        # Create target directory, if doesn't already exist
        try:
            os.makedirs(self.image_directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise JobException(f"Unable to create image directory {self.image_directory}: {e}")

        try:
            self.controller.initialize()
        except ControllerException as e:
            logger.error(e)
            raise JobException
        else:
            logger.info(f"{self.controller} initialized")

        try:
            self.camera.initialize()
        except CameraException as e:
            logger.error(e)
            raise JobException
        else:
            logger.info(f"{self.camera} initialized")

    def run(self):
        self.save_parameters()

        if self.is_interactive:
            try:
                self.interactive()
            except ControllerException as e:
                logger.error(e)
                raise JobException
        else:
            self.automatic()

    def move(self, waypoint):
        start_t = time()
        self.controller.move(waypoint)
        self.move_times.append(time() - start_t)
        sleep(self.wait_before)

    def acquire(self, waypoint):
        start_t = time()
        fn = f"{self.image_directory}/{len(self.image_times)}_{to_csv(waypoint)}"
        self.camera.acquire(filename=fn)
        self.image_times.append(time() - start_t)
        sleep(self.wait_after)
        return fn

    def automatic(self):
        logger.debug("Automatic mode enabled")
        logger.info(f"Saving to {self.image_directory}")
        for waypoint in self.sequence:
            # todo: temporary conversion until sequence class is refactored to dicts
            waypoint = {axis: f"{pos:.3f}" for axis, pos in waypoint if pos not in (None, '')}

            self.move(waypoint)
            self.acquire(waypoint)
            logger.info(f"{self.status()}, {to_csv(waypoint)}")

    def interactive(self):
        logger.info("Interactive mode enabled")
        commands = {
            "LEFT/RIGHT": "X",
            "UP/DOWN": "Y",
            "PAGE UP/PAGE DOWN": "Z",
            "+/-": "XY step size",
            "INSERT/DELETE": "Z step size",
            "HOME": "Return motors to configured home coordinate",
            "e/E": "Decrease/increase exposure time",
            "g/G": "Decrease/increase gain",
            "ENTER": "Save image",
            "p": "Get current position",
            "t": "Toggle position display",
            "r": "Reset controller",
            "f": "Display camera features",
            "s": "Display camera settings",
            "h": "Display this help",
            "q": "Quit"
        }
        log_dict(commands, banner="Interactive Commands")

        xy_ms_factor = 1
        z_ms_factor = 1
        pos_enabled = False

        while True:
            key = get_key()

            # Movements
            steps = 0
            if key == "left":
                steps = self.controller.jog('x', -xy_ms_factor)
            elif key == "right":
                steps = self.controller.jog('x', xy_ms_factor)
            elif key == "up":
                steps = self.controller.jog('y', xy_ms_factor)
            elif key == "down":
                steps = self.controller.jog('y', -xy_ms_factor)
            elif key == "page_up":
                steps = self.controller.jog('z', z_ms_factor)
            elif key == "page_down":
                steps = self.controller.jog('z', -z_ms_factor)
            elif key == "home":
                steps = self.controller.home()

            if steps and pos_enabled:
                logger.info(f"Position: {to_csv(self.controller.update_position())}")

            # Step Size
            if key == "+":
                xy_ms_factor += 1
                logger.info(f"XY step size: {xy_ms_factor * self.controller.motors['x'].microstep}")
            elif key == "-":
                xy_ms_factor = max(xy_ms_factor - 1, 1)
                logger.info(f"XY step size: {xy_ms_factor * self.controller.motors['x'].microstep}")
            elif key == "insert":
                z_ms_factor += 1
                logger.info(f"Z step size: {z_ms_factor * self.controller.motors['z'].microstep}")
            elif key == "delete":
                z_ms_factor = max(z_ms_factor - 1, 1)
                logger.info(f"Z step size: {z_ms_factor * self.controller.motors['z'].microstep}")

            # Camera
            if key == "e":
                t = self.camera.set("ExposureTime", perc=self.camera.settings['ExposureTime%'] - .01)
                logger.info(f"ExposureTime {t} microseconds ({self.camera.settings['ExposureTime%']:.2%})")
            elif key == "E":
                t = self.camera.set("ExposureTime", perc=self.camera.settings['ExposureTime%'] + .01)
                logger.info(f"ExposureTime {t} microseconds ({self.camera.settings['ExposureTime%']:.2%})")
            elif key == "g":
                t = self.camera.set("Gain", perc=self.camera.settings['Gain%'] - .01)
                logger.info(f"Gain {t} dB ({self.camera.settings['Gain%']:.2%})")
            elif key == "G":
                t = self.camera.set("Gain", perc=self.camera.settings['Gain%'] + .01)
                logger.info(f"Gain {t} dB ({self.camera.settings['Gain%']:.2%})")
            elif key == "f":
                log_dict(self.camera.features, banner="Camera Features")
            elif key == "s":
                log_dict(self.camera.settings, banner="Camera Settings")
            elif key in ("\n", "\r"):
                fn = self.acquire(self.controller.update_position())
                logger.info(f"Saved {', '.join(self.camera.save_formats)}: {fn}")

            # Other control
            if key == "p":
                logger.info(f"Position: {to_csv(self.controller.update_position())}")
            elif key == "t":
                pos_enabled = not pos_enabled
                logger.info(f"Position display {['disabled', 'enabled'][pos_enabled]}")
            elif key == "r":
                self.controller.reset()
                logger.info(f"Position: {to_csv(self.controller.update_position())}")
            elif key == "d":
                # Undocumented
                logger.setLevel(logging.DEBUG + logging.INFO - logger.level)
            elif key in ("?", "h"):
                log_dict(commands, banner="Interactive Commands")
            elif key in ("escape", "q", "ctrl-c"):
                break

            sleep(self.wait_after)
            self.camera.acquire()

    def save_parameters(self):
        with open(f"{self.image_directory}/parameters.json", "w") as fh:
            json.dump(self.parameters, fh, indent=2)

    @property
    def parameters(self):
        return dict(
            camera=self.camera.parameters,
            controller=self.controller.parameters,
            job=dict(
                name=self.name,
                mode=self.mode,
                path=self.path,
                wait_before=self.wait_before,
                wait_after=self.wait_after,
                sequence=self.sequence.waypoints
            )
        )

    def shutdown(self):
        self.controller.shutdown()
        self.camera.shutdown()

    def status(self):
        return (
            f"{len(self.move_times) / len(self.sequence):.2%}, "
            f"Waypoint {len(self.move_times)}/{len(self.sequence)}, "
            f"Time {self.elapsed}/{self.estimated}"
        )

    @property
    def elapsed(self):
        return datetime.now() - self.start_time

    @property
    def image_time_avg(self):
        try:
            return sum(self.image_times) / len(self.image_times)
        except ZeroDivisionError:
            return 0

    @property
    def estimated(self):
        step_time_t = (self.sequence.distance * self.controller.est_step_time)
        # todo: confirm est_move_time is needed
        process_time = sum([self.wait_before, self.wait_after, self.image_time_avg, self.controller.est_move_time])
        process_time_t = len(self.sequence) * process_time
        return timedelta(seconds=step_time_t + process_time_t)

    @property
    def is_interactive(self):
        return self.mode == "interactive"
