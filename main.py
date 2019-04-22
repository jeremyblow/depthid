import argparse
import logging
from typing import TextIO

from depthid.job import Job, JobException


logging.basicConfig(format="%(asctime)s [%(levelname)-5.5s] %(message)s")
logger = logging.getLogger("depthid")
logger.setLevel(logging.INFO)

# todo: test all the camera output formats
# todo: Test Bayer RG 16

# todo: new new
# todo: test faster intel python
# todo: re-enable full screen after screenshots are taken
# todo: can we record a full movie of the session?
#
# todo: be able to use m ui f display with panel arg
# todo: make sure jobs still work
# todo: speed up histogram display
# todo: acquire in interactive mode doesn't work
# tood: screen shot in interactive mode doesn't work
# todo: at fast FPS, the button display is too fast to see


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
