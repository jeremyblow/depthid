import logging
from threading import Thread
from time import time
from queue import Empty, Queue

import cv2
import numpy as np

# todo: this is spinnaker specific, improve
from depthid.cameras import CameraException
from depthid.controllers import ControllerException
from depthid.util import log_dict, to_csv


logger = logging.getLogger("depthid")


class UIException(Exception):
    pass


class UI:

    keymap = {
        13: 'enter',
        27: 'escape',
        2162688: 'page up',
        2228224: 'page down',
        2359296: 'home',
        2424832: 'left',
        2490368: 'up',
        2555904: 'right',
        2621440: 'down',
        2949120: 'insert',
        3014656: 'delete'
    }

    commands = {
        "LEFT/RIGHT": "X",
        "UP/DOWN": "Y",
        "PAGE UP/PAGE DOWN": "Z",
        "+/-": "XY step size",
        "INSERT/DELETE": "Z step size",
        "HOME": "Return motors to configured home coordinate",
        "e/E": "Decrease/increase exposure time",
        "g/G": "Decrease/increase gain",
        "a/A": "Decrease/increase % adjustment factor",
        "ENTER": "Save image",
        "p": "Get current position",
        "t": "Toggle position display",
        "r": "Reset controller",
        "f": "Display camera features and settings",
        "h": "Display this help",
        "q": "Quit"
    }

    # Interactive mode runtime controls
    xy_ms_factor = 1
    xy_step_size = 1.0
    z_ms_factor = 1
    z_step_size = 1.0
    pos_enabled = False
    adj_factor = .05
    running = True
    fps = 0

    # todo: get this dynamically
    win_w = 2560
    win_h = 1400
    main_w = 1920
    main_h = 1280
    edge_pad = 20
    menu = cv2.imread("depthid/assets/depthid_menu_16.png", cv2.IMREAD_UNCHANGED)
    menu_h, menu_w, menu_d = menu.shape
    menu_bottom = menu_h + edge_pad

    motor_clr = np.array([0, 98, 228]) * 256
    camera_clr = np.array([189, 52, 228]) * 256
    depthid_clr = np.array([35, 0, 230]) * 256

    def __init__(self, camera, controller, pipeline_callback):
        self.camera = camera
        self.controller = controller
        self.pipeline_callback = pipeline_callback
        self.q = Queue()

        # todo: decide on full screen or not
        # cv2.namedWindow("DepthID", cv2.WND_PROP_FULLSCREEN)
        # cv2.setWindowProperty("DepthID", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def interactive(self):
        logger.info("Interactive mode enabled")

        t = Thread(target=self.menu_loop)
        t.start()

        # todo: consider parameterizing the bit depth
        bg = np.zeros((self.win_h, self.win_w, 3), dtype=np.uint16)

        # Image area
        cv2.rectangle(bg, (0, 0), (self.main_w, self.main_h), (10000, 10000, 10000))

        self.display_menu(bg)

        while self.running:
            start = time()
            key = cv2.waitKeyEx(1)
            if key != -1:
                self.q.put(key)

            # todo: key spamming blocks redraw

            stack = self.pipeline_callback()

            self.display_main(bg, stack)
            self.display_panels(bg, (3, ), stack)

            # Stats bar
            self.fps = 1.0 / (time() - start)
            self.display_status(bg)
            cv2.imshow("DepthID", bg)

        t.join()

    def display_main(self, bg, stack):
        i = stack[2]
        h, w, d = i.shape
        bg[0:h, 0:w, :] = i

    def display_panels(self, bg, idxs: tuple, stack: list):
        h_offset = self.menu_bottom
        for i in idxs:
            img = stack[i]
            h, w, d = img.shape
            start_w = int((self.win_w - self.main_w - w) / 2) + self.main_w
            bg[h_offset:h_offset + h, start_w:start_w + w, :] = img
            h_offset += h

    def display_menu(self, img):
        # Menu center width
        start_w = int((self.win_w - self.main_w - self.menu_w) / 2) + self.main_w
        # Slight aesthetic nudge
        start_w += 25
        img[
            0 + self.edge_pad:self.menu_h + self.edge_pad,
            start_w:start_w + self.menu_w,
            :
        ] = self.menu

    def display_status(self, img, color=(65535, 65535, 65535)):
        panel_width = self.main_w
        panel_height = 115

        motor = f"Position: {to_csv(self.controller.position)} Step Size: {self.xy_step_size} xy {self.z_step_size} z"
        camera = (
            "Exposure: {ExposureTime:.6f} us ({ExposureTime%:.2%}) "
            "Gain: {Gain:.6f} dB ({Gain%:.2%}) "
            "Dimensions: {Width}x{Height} "
            "Format: {PixelFormat}"
        ).format(**self.camera.settings)
        depthid = f"FPS: {self.fps:.2f}"

        cv2.rectangle(img, (self.edge_pad, self.win_h - panel_height), (panel_width + self.edge_pad, self.win_h), (0,0,0), cv2.FILLED)
        cv2.putText(img, motor, (self.edge_pad, self.win_h - 85), cv2.FONT_HERSHEY_SIMPLEX, .8, self.motor_clr.tolist(), 1)
        cv2.putText(img, camera, (self.edge_pad, self.win_h - 50), cv2.FONT_HERSHEY_SIMPLEX, .8, self.camera_clr.tolist(), 1)
        cv2.putText(img, depthid, (self.edge_pad, self.win_h - 15), cv2.FONT_HERSHEY_SIMPLEX, .8, self.depthid_clr.tolist(), 1)

    def menu_loop(self):
        log_dict(self.commands, banner="Interactive Commands")

        while self.running:
            try:
                key = self.q.get(timeout=.01)
            except (Empty, TimeoutError):
                continue

            try:
                key = self.keymap[key]
            except KeyError:
                key = chr(key)

            try:
                self.handle_input(key)
            except (ControllerException, CameraException):
                self.running = False
                raise

    def handle_input(self, key):
        # todo: remove this
        # Movements
        steps = 0
        if key == "left":
            steps = self.controller.jog('x', -self.xy_ms_factor)
        elif key == "right":
            steps = self.controller.jog('x', self.xy_ms_factor)
        elif key == "up":
            steps = self.controller.jog('y', self.xy_ms_factor)
        elif key == "down":
            steps = self.controller.jog('y', -self.xy_ms_factor)
        elif key == "page up":
            steps = self.controller.jog('z', self.z_ms_factor)
        elif key == "page down":
            steps = self.controller.jog('z', -self.z_ms_factor)
        elif key == "home":
            steps = self.controller.home()

        if steps and self.pos_enabled:
            logger.info(f"Position: {to_csv(self.controller.update_position())}")

        # Step Size
        if key == "+":
            self.xy_ms_factor += 1
            self.xy_step_size = self.xy_ms_factor * self.controller.motors['x'].microstep
            logger.info(f"XY step size: {self.xy_step_size}")
        elif key == "-":
            self.xy_ms_factor = max(self.xy_ms_factor - 1, 1)
            self.xy_step_size = self.xy_ms_factor * self.controller.motors['x'].microstep
            logger.info(f"XY step size: {self.xy_step_size}")
        elif key == "insert":
            self.z_ms_factor += 1
            self.z_step_size = self.z_ms_factor * self.controller.motors['z'].microstep
            logger.info(f"Z step size: {self.z_step_size}")
        elif key == "delete":
            self.z_ms_factor = max(self.z_ms_factor - 1, 1)
            self.z_step_size = self.z_ms_factor * self.controller.motors['z'].microstep
            logger.info(f"Z step size: {self.z_step_size}")

        # Camera
        if key == "e":
            t = self.camera.set("ExposureTime", perc=self.camera.settings['ExposureTime%'] - self.adj_factor)
            logger.info(f"ExposureTime {t} microseconds ({self.camera.settings['ExposureTime%']:.2%})")
        elif key == "E":
            t = self.camera.set("ExposureTime", perc=self.camera.settings['ExposureTime%'] + self.adj_factor)
            logger.info(f"ExposureTime {t} microseconds ({self.camera.settings['ExposureTime%']:.2%})")
        elif key == "g":
            t = self.camera.set("Gain", perc=self.camera.settings['Gain%'] - self.adj_factor)
            logger.info(f"Gain {t} dB ({self.camera.settings['Gain%']:.2%})")
        elif key == "G":
            t = self.camera.set("Gain", perc=self.camera.settings['Gain%'] + self.adj_factor)
            logger.info(f"Gain {t} dB ({self.camera.settings['Gain%']:.2%})")
        elif key == "a":
            self.adj_factor = min(1, max(.01, self.adj_factor - .01))
            logger.info(f"Adjustment factor: {self.adj_factor:.2%}")
        elif key == "A":
            self.adj_factor = max(.01, min(1, self.adj_factor + .01))
            logger.info(f"Adjustment factor: {self.adj_factor:.2%}")
        elif key == "s":
            log_dict(self.camera.settings, banner="Camera Settings")
        elif key == "f":
            log_dict(self.camera.features, banner="Camera Features")
        elif key == "enter":
            # todo: this barfs
            fn = self.acquire(self.controller.update_position())
            logger.info(f"Saved {', '.join(self.camera.save_formats)}: {fn}")

        # Other control
        if key == "p":
            logger.info(f"Position: {to_csv(self.controller.update_position())}")
        elif key == "t":
            self.pos_enabled = not self.pos_enabled
            logger.info(f"Position display {['disabled', 'enabled'][self.pos_enabled]}")
        elif key == "r":
            self.controller.reset()
            logger.info(f"Position: {to_csv(self.controller.update_position())}")
        elif key == "d":
            # Undocumented
            logger.setLevel(logging.DEBUG + logging.INFO - logger.level)
        elif key in ("?", "h"):
            log_dict(self.commands, banner="Interactive Commands")
        elif key in ("escape", "q", "ctrl-c"):
            self.running = False

    def shutdown(self):
        self.running = False
