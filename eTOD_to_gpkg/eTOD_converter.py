"""Script to convert eTOD file in CSV format into geopackage (gpkg) format."""
import argparse
import logging

import geopandas
import geopandas as gpd
import pandas as pd

from coordinates_conversion import coordinates_to_point_wkt, longitude_to_dd, latitude_to_dd
from configuration import Configuration
from custom_logging import configure_logging
from errors import CoordinateValueError


def parse_args() -> argparse.Namespace:
    """Return parsed arguments"""
    parser = argparse.ArgumentParser(
        description=""""""
    )
    parser.add_argument("-i", "--input", type=str, required=False, help="Path to input eTOD CSV file")
    parser.add_argument("-o", "--output", type=str, required=False, help="Path to output geopackage file")
    parser.add_argument("-c", "--config", type=str, required=False, default="config.yml",
                        help="Path to configuration file, config.yml default")

    return parser.parse_args()


class eTODReader:

    def __init__(
            self,
            path_data: str,
            cfg: Configuration
    ) -> None:
        self._path_data = path_data
        """Path to CSV data file"""
        self._cfg = cfg
        """Parsed configuration"""

    def _get_columns_to_read(self) -> list[str]:
        """Returns columns which data will be captured.

        :return: columns which data will be captured as specified in configuration file
        :rtype: list
        """
        return list(self._cfg.column_map.keys()) + [self._cfg.col_lon, self._cfg.col_lat]

    def read_csv_data(self) -> pd.DataFrame:
        """Return data frame with raw data - only with columns as specified in configuration file.

        :return: raw data set
        :rtype: pd.DataFrame
        """
        return pd.read_csv(
            self._path_data,
            usecols=self._get_columns_to_read(),
            **self._cfg.file_settings
        )


class eTODConverter:

    def __init__(self, raw_data, cfg):
        self._raw_data: pd.DataFrame = raw_data
        self._cfg = cfg

    def drop_empty_coordinates(self) -> None:
        logging.info("Checking empty values in coordinates columns...")

        empty_coordinates = self._raw_data.loc[self._raw_data[self._cfg.col_lon].isnull()]
        self._raw_data.dropna(axis=0, subset=[self._cfg.col_lon, self._cfg.col_lat], inplace=True)

        if empty_coordinates.empty:
            logging.info("No missing data in coordinates columns detected")
        else:
            logging.info("Rows removed due to missing data in coordinates columns:\n{}".format(empty_coordinates))

    def rename_columns(self) -> None:
        self._raw_data.rename(columns=self._cfg.column_map, inplace=True)

    def _get_wkt_point(self, row: pd.Series) -> str:
        try:
            lon_dd = longitude_to_dd(row[self._cfg.col_lon])
            lat_dd = latitude_to_dd(row[self._cfg.col_lat])
        except CoordinateValueError as e:
            logging.info("{} row:\n {}".format(e, pd.DataFrame(row).T))
        else:
            return coordinates_to_point_wkt(lon_dd, lat_dd)

    def create_geometry_column(self) -> None:
        self._raw_data.insert(loc=len(self._raw_data.columns), column="coordinate_wkt", value="")
        self._raw_data["coordinate_wkt"] = self._raw_data.apply(
            lambda row: self._get_wkt_point(row),
            axis=1
        )

    def create_geodataframe(self) -> gpd.geodataframe:
        """"""
        self._raw_data["coordinates"] = geopandas.GeoSeries.from_wkt(self._raw_data["coordinate_wkt"])
        return gpd.GeoDataFrame(self._raw_data, geometry="coordinates")

    def to_geodataframe(self):
        self.drop_empty_coordinates()
        self.rename_columns()
        self.create_geometry_column()
        return self.create_geodataframe()


class DataSaver:

    def __init__(self, data: gpd.geodataframe):
        self._data = data

    def to_gpkg(self, path: str) -> None:
        self._data.to_file(path, crs="EPSG:4326")


def main(args_: argparse.Namespace) -> None:
    configure_logging()

    cfg = Configuration(args_.config)

    logging.info("Reading data from {}".format(args_.input))
    reader = eTODReader(args_.input, cfg)
    raw_data = reader.read_csv_data()

    converter = eTODConverter(raw_data, cfg)
    gdf = converter.to_geodataframe()

    saver = DataSaver(gdf)
    saver.to_gpkg(args_.output)


if __name__ == "__main__":
    args = parse_args()
    main(args)
