import csv
import re
from operator import sub


class Sequence:
    """Sequence of waypoints.

    Convenience methods to load or generate a sequence of waypoints from a set of coordinates or
    from sequence generation parameters. A waypoint is in the form:

        [(axis, position), (axis, position), (axis, position)]

    Where `axis` is a x, y, z, or w string, and `position` is an integer representing the position
    on the axis.

    Waypoints are typically loaded from a coordinate set contained in a list of coordinates, in the
    form:

        [(x, y, z, w), (x, y, z, w), (x, y, z, w)]

    Where x, y, z, and w are integers representing position on each axis. 1, 2, 3, or 4 dimensions
    are currently permitted as input.
    """

    axes = ('x', 'y', 'z', 'w')

    def __init__(self, waypoints: list=None):
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
        def do_axis(dimensions, axis, start, stop, step):
            for position in range(int(start), int(stop) + (1, -1)[int(step) < 0], int(step)):
                waypoint.append((axis, position))
                try:
                    yield from do_axis(dimensions[1:], **dimensions[1])
                except IndexError:
                    yield waypoint[:]
                finally:
                    waypoint.pop()

        p = re.compile(
            r'(?P<axis>[{}])\((?P<start>[\d-]+),(?P<stop>[\d-]+),(?P<step>[\d-]+)\),?'.format(''.join(cls.axes))
        )
        dimensions = [m.groupdict() for m in p.finditer(parameters)]
        return cls(
            waypoints=[x for x in do_axis(dimensions, **dimensions[0])]
        )

    def add(self, coordinate):
        waypoint = [(self.axes[idx], int(position)) for idx, position in enumerate(coordinate)]
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
