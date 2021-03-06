import csv
import re
from operator import sub


class Sequence:
    """Sequence of waypoints.

    Convenience methods to load or generate a sequence of waypoints from a set of coordinates or
    from sequence generation parameters. A waypoint is in the form:

        [(axis, position), (axis, position), (axis, position)]

    Where `axis` is a x, y, or z string, and `position` is an integer representing the position
    on the axis.

    Waypoints are typically loaded from a coordinate set contained in a list of coordinates, in the
    form:

        [(x, y, z), (x, y, z), (x, y, z)]

    Where x, y, and z are integers representing position on each axis. 1, 2, or 3 dimensions
    are currently permitted as input.
    """

    axes = ('x', 'y', 'z')

    def __init__(self, waypoints: list = None):
        self.waypoints = waypoints if waypoints is not None else []

    @classmethod
    def from_coordinates(cls, coordinates):
        sequence = cls()
        for coordinate in coordinates:
            sequence.add(coordinate)
        return sequence

    @classmethod
    def load_csv(cls, filename):
        with open(filename) as fh:
            return cls.from_coordinates(csv.reader(fh))

    @classmethod
    def generate(cls, parameters):
        waypoint = []

        def do_axis(dims, axis, start, stop, step):
            # todo: add infinite loop avoidance
            stop_v = float(stop)
            curr_v = float(start)
            step_v = float(step)
            positions = [curr_v]
            while True:

                if step_v < 0:
                    # Descending
                    if curr_v <= stop_v:
                        # Limit reached
                        break
                    else:
                        curr_v += step_v
                        positions.append(curr_v)
                elif step_v > 0:
                    # Ascending
                    if curr_v >= stop_v:
                        # Limit reached
                        break
                    else:
                        curr_v += step_v
                        positions.append(curr_v)
                else:
                    # No action, we're done
                    break

            for position in positions:
                waypoint.append((axis, position))
                try:
                    yield from do_axis(dims[1:], **dims[1])
                except IndexError:
                    yield waypoint[:]
                finally:
                    waypoint.pop()

        p = re.compile(
            r'(?P<axis>[{}])\((?P<start>[\d.-]+),(?P<stop>[\d.-]+),(?P<step>[\d.-]+)\),?'.format(''.join(cls.axes))
        )
        dimensions = [m.groupdict() for m in p.finditer(parameters)]
        sequence = cls(
            waypoints=[x for x in do_axis(dimensions, **dimensions[0])]
        )
        return sequence

    def add(self, coordinate):
        waypoint = [(self.axes[idx], int(p)) for idx, p in enumerate(coordinate) if p not in (None, '')]
        self.waypoints.append(waypoint)
        return waypoint

    @property
    def distance(self):
        origin = self.waypoints[0]
        distance = 0
        for waypoint in self.waypoints[1:]:
            distance += max(map(sub, [c[1] for c in waypoint], [c[1] for c in origin]))
            origin = waypoint
        return distance

    def __iter__(self):
        for waypoint in self.waypoints:
            yield waypoint

    def __len__(self):
        return len(self.waypoints)

    def __bool__(self):
        return bool(len(self.waypoints))
