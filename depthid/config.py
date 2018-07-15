import json


def load_config(config_fh):
    with config_fh as fh:
        return json.load(fh)