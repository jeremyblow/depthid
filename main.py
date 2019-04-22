import argparse
import logging
from typing import TextIO

from depthid.job import Job, JobException


logging.basicConfig(format="%(asctime)s [%(levelname)-5.5s] %(message)s")
logger = logging.getLogger("depthid")
logger.setLevel(logging.INFO)

# todo: be able to repeat previous session by using parameters.json
# todo: add command to reset to 0,0,0, homing doesn't work, figure out persistence
# todo: clean camera up parameters
# todo: test all the camera output formats
# todo: refactor wait_before/wait_after canon
# todo: Test Bayer RG 16

# new todo:
# todo: need to pass image info into display call


def main(config_fh: TextIO):
    job = Job.load(config_fh)

    try:
        job.initialize()
    except JobException:
        logger.error(f"Job encountered a problem during initialization, shutting down")
        job.shutdown()
        exit(1)

    try:
        job.run()
    except JobException:
        logger.error(f"Job encountered a problem during run, shutting down")
    except KeyboardInterrupt:
        logger.info("Job cancelled due to keyboard interrupt")
    finally:
        job.shutdown()


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
    args = parser.parse_args()

    try:
        main(**vars(args))
    except RuntimeError as e:
        exit(f"Problem: {e}")
