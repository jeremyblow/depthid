import argparse
from typing import TextIO

from depthid.job import Job
from depthid.camera import Camera
from depthid.config import load_config
from depthid.controller import Controller


def main(config_fh: TextIO, job_fh: TextIO):
    config = load_config(config_fh)
    job = Job.load(
        job_fh=job_fh,
        controller=Controller(**config['controller']),
        camera=Camera(**config['camera']),
    )
    job.setup()
    try:
        job.run()
    except KeyboardInterrupt:
        job.shutdown()
        exit("Job cancelled due to keyboard interrupt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python main.py",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--config',
        dest='config_fh',
        type=argparse.FileType('r'),
        help='JSON configuration filename',
        required=True
    )
    parser.add_argument(
        '--job',
        dest='job_fh',
        type=argparse.FileType('r'),
        help='JSON job filename',
        required=True
    )
    args = parser.parse_args()

    try:
        main(**vars(args))
    except RuntimeError as e:
        exit(f"Problem: {e}")