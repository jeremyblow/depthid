from .controller import Controller
from .exception import ControllerException


class Marlin(Controller):
    banner = "Marlin"

    def update_position(self):
        # todo: describe behavior
        self.send("M114", send_linefeed=False)
        message = self.receive()
        message = self.receive()
        message = self.receive()
        try:
            m = self.pos_pattern.search(message).groupdict()
        except AttributeError:
            raise ControllerException(f"Unexpected output while determining motor position: {message}")
        else:
            self.position.update(**{k: f"{float(v):.3f}" for k, v in m.items() if v is not None})
        return m