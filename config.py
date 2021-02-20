import configparser
from dataclasses import dataclass


@dataclass
class Config():
    """Class for keeping track of a verification session."""
    token: str
    prefix: str
    check_interval: int
    expiry_seconds: int
    url: str


def read() -> Config:
    """Read the config."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    # TODO: error handling

    return Config(
        token=config['MAIN']['Token'],
        prefix=config['MAIN']['Prefix'],
        check_interval=int(config['MAIN'].get('CheckInterval', 60)),
        expiry_seconds=int(config['MAIN'].get('ExpirySeconds', 43200)),  # 12h
        url=config['MAIN'].get("url", "http://127.0.0.1:5000"),
    )
