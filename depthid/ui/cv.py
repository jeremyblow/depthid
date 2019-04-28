import logging
from threading import Thread
from time import time
from queue import Empty, Queue

import cv2
import numpy as np

from depthid import job
from depthid.cameras import CameraException
from depthid.controllers import ControllerException
from depthid.pipeline.scikit import convert_uint8_uint16
from depthid.ui import UIException
from depthid.util import log_dict, to_csv


logger = logging.getLogger("depthid")


class UI:

    keymap = {
        13: "enter",
        32: "space",
        43: "plus",
        45: "minus",
        65: "a_upper",
        69: "e_upper",
        71: "g_upper",
        97: "a",
        101: "e",
        103: "g",
        113: "q",
        2162688: "page_up",
        2228224: "page_down",
        2359296: "home",
        2424832: "left",
        2490368: "up",
        2555904: "right",
        2621440: "down",
        2949120: "insert",
        3014656: "delete"
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

    # todo: get these dynamically
    win_w = 2560
    win_h = 1400
    win_channels = 3
    win_dtype = np.uint16

    # min_h, min_w, max_h, max_w
    panel_map = {
        "main_border": (0, 0, 1201, 1921),
        "main": (1, 1, 1280, 1920),
        "sub1": (0, 1922, win_h - 1, win_w - 1),
        "sub2": (int(win_h * .33), 1922, int(win_h * .66), win_w - 1),
        "sub3": (int(win_h * .66), 1922, win_h, win_w - 1),
        "status": (1202, 0, win_h - 1, win_w - 1)
    }

    # Interactive mode runtime controls
    xy_ms_factor = 1
    z_ms_factor = 1
    pos_enabled = False
    adj_factor = .05
    last_key = None
    last_bg = None
    last_main = None
    running = True
    fps = 0

    main_w = 1920
    main_h = 1200
    edge_pad = 20
    asset_dir = "depthid/assets/menu_images/"
    menu = convert_uint8_uint16(cv2.imread(f"{asset_dir}/depthid_menu.png", cv2.IMREAD_UNCHANGED))
    menu_h, menu_w, menu_d = menu.shape
    menu_bottom = menu_h + edge_pad
    for key in keymap.values():
        vars()[f"menu_{key}"] = convert_uint8_uint16(cv2.imread(f"{asset_dir}/depthid_menu_{key}.png", cv2.IMREAD_UNCHANGED))

    # BGR
    scale = 65536
    motor_clr = np.array([0.895, 0.383, 0.00]) * scale
    camera_clr = np.array([0.894, 0.205, 0.739]) * scale
    depthid_clr = np.array([0.0, 0.136, .904]) * scale
    white_clr = np.array([1, 1, 1]) * scale

    def __init__(self, camera, controller, job, full_screen=True):
        self.camera = camera
        self.controller = controller
        self.job = job
        self.q = Queue()
        self.xy_step_size = self.controller.motors['x'].microstep
        self.z_step_size = self.controller.motors['z'].microstep

        # Generate window image and main panel border
        self.bg = np.zeros((self.win_h, self.win_w, self.win_channels), dtype=self.win_dtype)
        cv2.rectangle(self.bg, self.panel_map['main_border'][:2], self.panel_map['main_border'][3:1:-1], self.white_clr.tolist())

        if full_screen:
            cv2.namedWindow("DepthID", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("DepthID", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def interactive(self):
        logger.info("Interactive mode enabled")

        t = Thread(target=self.menu_loop)
        t.start()

        while self.running:
            start = time()

            key = cv2.waitKeyEx(1)
            if key != -1:
                try:
                    key = self.keymap[key]
                except KeyError:
                    key = chr(key)
                self.q.put(key)

            # todo: key spamming blocks redraw

            try:
                self.job.do_pipeline()
            except job.JobException:
                self.running = False
            else:
                self.refresh()
                self.fps = 1.0 / (time() - start)

        t.join()

    def refresh(self, wait_key=False):
        cv2.imshow("DepthID", self.bg)
        self.last_bg = self.bg.copy()
        if wait_key:
            return cv2.waitKey(1)

    def display(self, data: np.ndarray, panel: str, l_offset: int = 0, t_offset: int = 0, **state):
        min_h, min_w, max_h, max_w = self.panel_map[panel]
        image_h, image_w, image_d = data.shape
        try:
            self.bg[
                min_h + t_offset:min_h + t_offset + image_h,
                min_w + l_offset:min_w + l_offset + image_w,
                :
            ] = data
        except ValueError as e:
            raise UIException(
                f"Failed to render, this is usually due a pipeline sequence misconfiguration, "
                f"or a transformation error. Reason: {e}"
            )

        if panel == "main":
            self.last_main = data
        return data

    def display_menu(self, panel: str = "status", **state):
        data = getattr(self, f"menu_{self.last_key}", self.menu)
        self.display(data, panel, l_offset=75, t_offset=25)
        self.last_key = None
        return data

    def display_status(self, x_pos, y_pos, z_pos, panel: str = "status", **state):
        panel_w = self.main_w
        panel_h = 140
        font = cv2.FONT_HERSHEY_SIMPLEX, .7

        if self.job.status == 3:
            depthid = f"Job: {self.job.status()}"
            camera = (
                "Exposure: {ExposureTime:.6f} us ({ExposureTime%:.2%}) "
                "Gain: {Gain:.6f} dB ({Gain%:.2%}) "
                "Dimensions: {Width}x{Height} "
                "Format: {PixelFormat}"
            ).format(adj=self.adj_factor, **self.camera.settings)
            motor = (
                f"Position: {x_pos}, {y_pos}, {z_pos} "
            )
        else:
            depthid = f"FPS: {self.fps:.2f} PipelineT: {self.job.pipeline_t}"
            camera = (
                "Exposure: {ExposureTime:.6f} us ({ExposureTime%:.2%}) "
                "Gain: {Gain:.6f} dB ({Gain%:.2%}) "
                "AdjFactor: {adj:.0%} "
                "Dimensions: {Width}x{Height} "
                "Format: {PixelFormat}"
            ).format(adj=self.adj_factor, **self.camera.settings)
            motor = (
                f"Position: {', '.join([str(p) for p in self.controller.position.values()])} "
                f"Step Size: {self.xy_step_size}, {self.xy_step_size}, {self.z_step_size} "
                f"Microstep: {', '.join([str(m.microstep) for m in self.controller.motors.values()])}"
            )
        directory = f"Directory: {self.job.session_directory}"

        data = np.zeros((panel_h, panel_w, self.win_channels))
        cv2.putText(data, motor, (0, 30), *font, self.motor_clr.tolist(), 1)
        cv2.putText(data, camera, (0, 60), *font, self.camera_clr.tolist(), 1)
        cv2.putText(data, depthid, (0, 90), *font, self.depthid_clr.tolist(), 1)
        cv2.putText(data, directory, (0, 120), *font, self.depthid_clr.tolist(), 1)
        self.display(data, panel, l_offset=15, t_offset=10)
        return data

    def menu_loop(self):
        log_dict(self.commands, banner="Interactive Commands")

        while self.running:
            try:
                key = self.q.get(timeout=.01)
            except (Empty, TimeoutError):
                continue

            try:
                self.handle_input(key)
            except (ControllerException, CameraException):
                self.running = False
                raise

    def handle_input(self, key):
        self.last_key = key

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
        elif key == "page_up":
            steps = self.controller.jog('z', self.z_ms_factor)
        elif key == "page_down":
            steps = self.controller.jog('z', -self.z_ms_factor)
        elif key == "home":
            steps = self.controller.home()

        if steps and self.pos_enabled:
            logger.info(f"Position: {to_csv(self.controller.update_position())}")

        # Step Size
        if key == "plus":
            self.xy_ms_factor += 1
            self.xy_step_size = self.xy_ms_factor * self.controller.motors['x'].microstep
            logger.info(f"XY step size: {self.xy_step_size}")
        elif key == "minus":
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
        elif key == "e_upper":
            t = self.camera.set("ExposureTime", perc=self.camera.settings['ExposureTime%'] + self.adj_factor)
            logger.info(f"ExposureTime {t} microseconds ({self.camera.settings['ExposureTime%']:.2%})")
        elif key == "g":
            t = self.camera.set("Gain", perc=self.camera.settings['Gain%'] - self.adj_factor)
            logger.info(f"Gain {t} dB ({self.camera.settings['Gain%']:.2%})")
        elif key == "g_upper":
            t = self.camera.set("Gain", perc=self.camera.settings['Gain%'] + self.adj_factor)
            logger.info(f"Gain {t} dB ({self.camera.settings['Gain%']:.2%})")
        elif key == "a":
            self.adj_factor = min(1.0, max(.01, self.adj_factor - .01))
            logger.info(f"Adjustment factor: {self.adj_factor:.2%}")
        elif key == "a_upper":
            self.adj_factor = max(.01, min(1, self.adj_factor + .01))
            logger.info(f"Adjustment factor: {self.adj_factor:.2%}")
        elif key == "s":
            log_dict(self.camera.settings, banner="Camera Settings")
        elif key == "f":
            log_dict(self.camera.features, banner="Camera Features")
        elif key == "enter":
            self.job.save(self.last_main, use_opencv=True, **self.job.state)
        elif key == "space":
            # todo: generalize this
            self.job.save(self.last_bg, use_opencv=True, **self.job.state)

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
        elif key == "q":
            self.running = False

    def shutdown(self):
        self.running = False
