"""Common classes, function etc. used across 'IMGW` scripts"""
from pathlib import Path

from pydantic import BaseModel
from yaml import safe_load

MONTH_RANGE = list(range(1, 13))


class DataRange(BaseModel):
    """
    Define data range for which download data.

    Attributes:
        from_year: beginning year to fetch data
        to_year: end year to fetch data
    """
    from_year: int
    to_year: int


class Configuration(BaseModel):
    """
    Scripts configuration.

    Attributes:
        data_base_url: IMGW URL to fetch data from
        data_dir: path to directory where raw data (fetched from IMGW) will be saved
        range: data range (years) for which fetch data
    """

    data_base_url: str
    data_dir: Path
    range: DataRange


def load_config(path: Path = Path("config.yaml")) -> Configuration:
    """Load configuration from YAML file.

    :param path: path to the configuration file
    :return: parsed configuration file, instance of Configuration
    """
    content = safe_load(path.read_text(encoding="utf-8"))
    return Configuration(**content)
