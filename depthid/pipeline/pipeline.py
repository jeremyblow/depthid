def noop(x_pos, y_pos, z_pos, x_min=None, x_max=None, y_min=None, y_max=None, z_min=None, z_max=None, **state):
    """Returns true if any position is outside any specified limit."""
    return (
        (x_min is not None and (x_pos < x_min))
        or (x_max is not None and (x_pos > x_max))
        or (y_min is not None and (y_pos < y_min))
        or (y_max is not None and (y_pos > y_max))
        or (z_min is not None and (z_pos < z_min))
        or (z_max is not None and (z_pos > z_max))
    )