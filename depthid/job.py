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
from depthid.ui import UIException, cv
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
        self.ui = cv.UI(camera=camera, controller=controller, job=self, full_screen=full_screen)

        self.save_ctr = 0
        self.move_ctr = 0
        self.state = {}

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

            # State dict to be made available to all pipeline operations.
            # A pipeline operation may add any of these keys to its signature to
            # use current value. All pipeline operations must have a **state arg
            # in their signature so that non-applicable keys can be ignored.
            #
            # The reason for this is not just a local variable is so that the UI
            # module can inject state, since it calls some pipeline functions
            # directly.

            self.state = {
                'x_pos': float(self.controller.position['x']),
                'y_pos': float(self.controller.position['y']),
                'z_pos': float(self.controller.position['z']),
                'pos': self.controller.position
            }

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

            args = []
            if i is not None:
                args = [i]

            try:
                stack[idx] = fn(*args, **step.get("kw", {}), **self.state)
            except UIException as e:
                logger.error(f"UI error during {idx}-{step['m']}-{step['f']}: {e}")
                raise JobException
            except Exception:
                logging.exception(f"Unhandled exception during pipeline exec of {idx}-{step['m']}-{step['f']}")
                raise

            self.pipeline[idx]["time"] = time() - start

            # Special run-time handlers
            if step['m'] == "pipeline":
                if step['f'] == "noop" and stack[idx]:
                    break
                elif step['f'] == "kill" and stack[idx]:
                    raise JobException(f"Job killed due to exceeded limit, {self.pos}, limit {step['kw']}")

        self.pipeline_t = ", ".join([f"{v['time']:.3f}" for v in self.pipeline])
        return stack

    def save(self, data, x_pos, y_pos, z_pos, formats=None, use_opencv=False, **kwargs):

        for fmt in formats or self.save_formats:
            fn = f"{self.session_directory}/{self.save_ctr}_{x_pos},{y_pos},{z_pos}.{fmt}"

            # todo: have this behavior expressed via the camera class
            if isinstance(self.camera, OpenCV) or use_opencv:
                p.opencv.save(data, fn)
            elif isinstance(self.camera, Spinnaker):
                p.spinnaker.save(data, fn)

            self.save_ctr += 1
            logger.info(f"Saved {fn}")

    def automatic(self):
        logger.info("Automatic mode enabled")

        for waypoint in self.sequence:
            # todo: temporary conversion until sequence class is refactored to dicts
            waypoint = {axis: f"{pos:.3f}" for axis, pos in waypoint if pos not in (None, '')}

            self.controller.move(waypoint)
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

    @property
    def pos(self):
        return self.controller.position
