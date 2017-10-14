from datetime import datetime
from time import time

from depthid import capture, get_properties, move, setup, tear_down


def main():
    """
    The below is an example process which steps forward 3 steps 100 times, taking and
    displaying a picture after each step. Then, it brings the camera back to its original
    position by taking a single -600 step back. Finally, we tear down the connections
    and display a summary of the operation.
    """

    # Setup and obtain serial device connection, camera capture instance and path to save files
    serial_device, cam, path = setup()

    # Specify parameters for this session
    session = datetime.now().isoformat()
    start_time = time()
    step_size = 2
    count = 300

    # Perform camera movements and image capture
    for offset in range(1, count + 1):
        move(serial_device=serial_device, steps=step_size)
        capture(camera=cam, path=path, session_label=session, image_label=str(offset * step_size))

    # Reset the camera back to original position and tear down serial and camera connections
    move(serial_device=serial_device, steps=-(step_size * count))
    tear_down(serial_device=serial_device, camera=cam)

    # Display summary information about this session
    duration = time() - start_time
    rate = count / duration
    parameters = get_properties(cam)
    print(f"{session}: {count} images saved in {duration}s ({rate}/s) using {parameters}.")


if __name__ == "__main__":
    main()