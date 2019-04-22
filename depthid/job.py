import errno
import json
import logging
import os
from datetime import datetime
from time import time

from depthid import pipeline as p
from depthid.cameras import Camera, CameraException, load_camera
from depthid.controllers import Controller, ControllerException, load_controller
from depthid.sequence import Sequence
from depthid.ui.cv import UI as CVUI
from depthid.util import pathify


logger = logging.getLogger("depthid")


class JobException(Exception):
    pass


class Job:

    def __init__(self, name: str, path: str, controller: Controller, camera: Camera, pipeline: dict, parameters: str,
                 csv_filename: str = None, sequence_parameters: str = None, coordinates: list = None,
                 mode: str = "automatic", full_screen: bool = True):

        self.start_time = datetime.now()
        self.name = f"{name}_{self.start_time.isoformat().replace(':', '')}"
        self.mode = mode
        self.path = pathify(path)
        self.session_directory = f"{self.path}/{self.name}"
        self.parameters = parameters
        self.controller = controller
        self.camera = camera
        self.pipeline = pipeline
        self.pipeline_t = ""

        # todo: consider pushing this out to main
        self.ui = CVUI(camera=camera, controller=controller, job=self, full_screen=full_screen)

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
    def load(cls, config_fh):

        with config_fh as fh:
            d = fh.read()

        config = json.loads(d)

        return cls(
            controller=load_controller(**config['controller']),
            camera=load_camera(**config['camera']),
            parameters=d,
            **config['job']
        )

    def initialize(self):
        # Create target directory, if doesn't already exist
        try:
            os.makedirs(self.session_directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise JobException(f"Unable to create image directory {self.session_directory}: {e}")

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

        # Bind ui instance to pipeline module so that ui can be referenced at runtime
        p.ui = self.ui

        self.save_parameters()

    def run(self):
        logger.info(f"Saving session to {self.session_directory}")

        if self.is_interactive:
            try:
                self.ui.interactive()
            except (CameraException, ControllerException) as e:
                logger.error(e)
                raise JobException
        # else:
        #     self.automatic()

    def do_pipeline(self):
        stack = [None] * len(self.pipeline)
        for idx, step in enumerate(self.pipeline):
            start = time()

            # User is asked to specify "camera" for i val, which raises TypeError
            # allowing us to inject the dependency
            try:
                i = stack[step['i']]
            except KeyError:
                i = None
            except TypeError:
                # todo: this is fragile, think of a better way to generalize
                i = self.camera.camera

            fn = getattr(getattr(p, step['m']), step['f'])

            if i is not None:
                stack[idx] = fn(i, **step.get("kw", {}))
            else:
                stack[idx] = fn(**step.get("kw", {}))

            self.pipeline[idx]["time"] = time() - start

        self.pipeline_t = ", ".join([f"{v['time']:.2f}" for v in self.pipeline])
        return stack

    def move(self, waypoint):
        start_t = time()
        self.controller.move(waypoint)
        self.move_times.append(time() - start_t)

    # def acquire(self, waypoint):
    #     start_t = time()
    #     fn = f"{self.image_directory}/{len(self.image_times)}_{to_csv(waypoint)}"
    #     self.camera.acquire(filename=fn)
    #     self.image_times.append(time() - start_t)
    #     return fn

    # def automatic(self):
    #     logger.debug("Automatic mode enabled")
    #     logger.info(f"Saving to {self.image_directory}")
    #     log_dict(self.camera.settings, banner="Camera Settings")
    #     for waypoint in self.sequence:
    #         # todo: temporary conversion until sequence class is refactored to dicts
    #         waypoint = {axis: f"{pos:.3f}" for axis, pos in waypoint if pos not in (None, '')}
    #
    #         self.move(waypoint)
    #         self.acquire(waypoint)
    #         logger.info(f"{self.status()}, {to_csv(waypoint)}")
    #
    #     logger.info(f"Returning to home 0,0,0")
    #     self.move({'x': '0.000', 'y': '0.000', 'z': '0.000'})

    def save_parameters(self):
        with open(f"{self.session_directory}/parameters.json", "w") as fh:
            fh.write(self.parameters)

    def shutdown(self):
        self.controller.shutdown()
        self.camera.shutdown()

    # def status(self):
    #     return (
    #         f"{len(self.move_times) / len(self.sequence):.2%}, "
    #         f"Waypoint {len(self.move_times)}/{len(self.sequence)}, "
    #         f"Time {self.elapsed}/{self.estimated}"
    #     )

    @property
    def elapsed(self):
        return datetime.now() - self.start_time

    @property
    def image_time_avg(self):
        try:
            return sum(self.image_times) / len(self.image_times)
        except ZeroDivisionError:
            return 0

    # @property
    # def estimated(self):
    #     step_time_t = (self.sequence.distance * self.controller.est_step_time)
    #     # todo: confirm est_move_time is needed
    #     process_time = sum([self.wait_before, self.wait_after, self.image_time_avg, self.controller.est_move_time])
    #     process_time_t = len(self.sequence) * process_time
    #     return timedelta(seconds=step_time_t + process_time_t)

    @property
    def is_interactive(self):
        return self.mode == "interactive"
