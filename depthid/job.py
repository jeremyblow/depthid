import errno
import json
import os
from datetime import datetime, timedelta
from time import sleep, time

from depthid.camera import Camera
from depthid.controller import Controller
from depthid.sequence import Sequence


class Job:

    def __init__(self, name: str, path: str, image_format: str, display: bool, wait_before: float, wait_after: float,
                 controller: Controller, camera: Camera, csv_filename: str=None, sequence_parameters: str=None,
                 coordinates: list=None):

        self.start_time = datetime.now()
        self.name = f"{name}_{self.start_time.isoformat()}"
        self.path = path if path.endswith('/') else f"{path}/"
        self.image_format = image_format
        self.display = display
        self.wait_before = wait_before
        self.wait_after = wait_after
        self.controller = controller
        self.camera = camera

        # Statistics
        self.step_count = 0
        self.image_times = []

        if csv_filename:
            self.sequence = Sequence.load_csv(csv_filename)
        elif sequence_parameters:
            self.sequence = Sequence.generate(sequence_parameters)
        elif coordinates:
            self.sequence = Sequence.from_coordinates(coordinates)
        else:
            raise RuntimeError("Either CSV filename, sequence parameters, or coordinates must be provided")

    @classmethod
    def load(cls, job_fh, controller: Controller, camera: Camera):
        with job_fh as fh:
            kwargs = json.load(fh)
        return cls(
            controller=controller,
            camera=camera,
            **kwargs
        )

    def setup(self):
        # Create target directory, if doesn't already exist
        try:
            os.makedirs(self.image_directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def run(self):
        self.controller.initialize()
        self.camera.initialize()
        self.save_parameters()

        for idx, waypoint in enumerate(self.sequence):
            command = self.controller.move(waypoint)

            sleep(self.wait_before)

            start_t = time()
            img = self.camera.capture()
            if self.display:
                self.camera.display(img)
            if all([self.path, self.image_format]):
                self.camera.save(
                    img=img,
                    filename=f"{self.image_directory}/{idx}_{command}.{self.image_format}"
                )
            self.image_times.append(time() - start_t)

            sleep(self.wait_after)

            self.step_count += 1
            print(f"{self.status()}, {[p for _, p in waypoint]}")

    def save_parameters(self):
        with open(f"{self.image_directory}/parameters.json", "w") as fh:
            json.dump(self.parameters, fh)

    @property
    def parameters(self):
        return dict(
            camera=self.camera.parameters,
            controller=self.controller.parameters,
            job=dict(
                name=self.name,
                path=self.path,
                image_format=self.image_format,
                display=self.display,
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
            f"{self.step_count / len(self.sequence):.2%}, "
            f"Waypoint {self.step_count}/{len(self.sequence)}, "
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
    def image_directory(self):
        return f"{self.path}{self.name}"

    @property
    def estimated(self):
        step_time_t = (self.sequence.distance * self.controller.est_step_time)
        process_time = sum([self.wait_before, self.wait_after, self.image_time_avg, self.controller.est_move_time])
        process_time_t = len(self.sequence) * process_time
        return timedelta(seconds=step_time_t + process_time_t)
