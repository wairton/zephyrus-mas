import json


def load(config_path, config_environment=None):
    with open(config_path) as config_file:
        config = json.load(config_file)

    if config_environment is not None:
        for env_key, env_value in config_environment.items():
            if not env_key.startswith("$"):
                env_key = "${}".format(env_key)
            for k in list(config.keys()):
                config[k] = config[k].replace(env_key, env_value)
    return config
