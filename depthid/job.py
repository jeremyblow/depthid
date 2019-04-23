import errno
import json
import logging
import os
from datetime import datetime
from time import time

from depthid import pipeline as p
from depthid.cameras import Camera, CameraException, OpenCV, Spinnaker, load_camera
from depthid.controllers import Controller, ControllerException, load_controller
from depthid.sequence import Sequence
from depthid.ui.cv import UI as CVUI
from depthid.util import pathify, to_csv


logger = logging.getLogger("depthid")


class JobException(Exception):
    pass


class Job:

    def __init__(self, name: str, path: str, controller: Controller, camera: Camera, pipeline: dict, parameters: str,
                 csv_filename: str = None, sequence_parameters: str = None, coordinates: list = None,
                 mode: str = "automatic", full_screen: bool = True, save_formats: list = None):

        self.start_time = datetime.now()
        self.name = f"{name}_{self.start_time.isoformat().replace(':', '')}"
        self.mode = mode
        self.path = pathify(path)
        self.session_directory = f"{self.path}/{self.name}"
        self.save_formats = save_formats or ["raw"]
        self.parameters = parameters
        self.controller = controller
        self.camera = camera
        self.pipeline = pipeline
        self.pipeline_t = ""

        # todo: consider pushing this out to main
        self.ui = CVUI(camera=camera, controller=controller, job=self, full_screen=full_screen)

        self.save_ctr = 0
        self.move_ctr = 0
        self.last_waypoint = None

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
        p.job = self

        self.save_parameters()

    def run(self):
        logger.info(f"Saving session to {self.session_directory}")

        if self.is_interactive:
            try:
                self.ui.interactive()
            except (CameraException, ControllerException) as e:
                logger.error(e)
                raise JobException
        else:
            self.automatic()

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

        self.pipeline_t = ", ".join([f"{v['time']:.3f}" for v in self.pipeline])
        return stack

    def save(self, data, formats=None, pos=None):
        # todo: improve var passing in pipeline so pos can be passed more easily
        pos = pos if pos is not None else self.last_waypoint

        for fmt in formats or self.save_formats:
            fn = f"{self.session_directory}/{self.save_ctr}_{to_csv(pos)}.{fmt}"

            # todo: have this behavior expressed via the camera class
            if isinstance(self.camera, Spinnaker):
                p.spinnaker.save(data, fn)
            elif isinstance(self.camera, OpenCV):
                p.opencv.save(data, fn)

            self.save_ctr += 1
            logger.info(f"Saved {fn}")

    def automatic(self):
        logger.info("Automatic mode enabled")

        for waypoint in self.sequence:
            # todo: temporary conversion until sequence class is refactored to dicts
            waypoint = {axis: f"{pos:.3f}" for axis, pos in waypoint if pos not in (None, '')}

            self.controller.move(waypoint)
            self.last_waypoint = waypoint
            self.move_ctr += 1
            self.do_pipeline()
            self.ui.refresh(wait_key=True)
            logger.info(f"{self.status()}, {to_csv(waypoint)}")

        logger.info(f"Returning to home 0,0,0")
        self.controller.move({'x': '0.000', 'y': '0.000', 'z': '0.000'})

    def save_parameters(self):
        with open(f"{self.session_directory}/parameters.json", "w") as fh:
            fh.write(self.parameters)

    def shutdown(self):
        self.controller.shutdown()
        self.camera.shutdown()

    def status(self):
        if len(self.sequence) == 0:
            return ""

        complete = self.move_ctr / len(self.sequence)
        estimated = str(self.elapsed / complete).split('.')[0]
        return (
            f"{complete:.2%}, "
            f"Waypoint {self.move_ctr}/{len(self.sequence)}, "
            f"Time {str(self.elapsed).split('.')[0]}/{estimated}"
        )

    @property
    def elapsed(self):
        return datetime.now() - self.start_time

    @property
    def is_interactive(self):
        return self.mode == "interactive"
