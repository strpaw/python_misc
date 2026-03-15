"""Script to dump temperature data (daily average) for given month and station.

Example usage, dump data for Gdańsk-Rębiechowo (station code 254180090, May for data downloaded from
https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/terminowe/klimat
into dir imgw_data

python .\dump_month_daily_avg_temp.py -d imgw_data -m May -s 254180090
or
python .\dump_month_daily_avg_temp.py -d imgw_data -m May -s Gdańsk-Rębiechowo
"""
import argparse
from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd


IMGW_STATIONS_WFS = ("https://imgw.isok.gov.pl/wss/INSPIRE/INSPIRE_EF_SZS_WFS"
                    "?service=wfs"
                    "&version=2.0.0"
                    "&request=GetFeature"
                    "&typeName=ef:EnvironmentalMonitoringFacility")
MONTHS = {
    "JAN" : 1,
    "FEB" : 2,
    "MAR" : 3,
    "APR" : 4,
    "MAY" : 5,
    "JUN" : 6,
    "JUL" : 7,
    "AUG" : 8,
    "SEP" : 9,
    "OCT" : 10,
    "NOV" : 11,
    "DEC" : 12
}


def arg_int_or_str(value) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def parse_args() -> argparse.Namespace:
    """
    Parse  script arguments.

    :return: script arguments with values
    """
    parser = argparse.ArgumentParser(description="Dump avg daily temperature data for given station and month")
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        default="data",
        help="Path to data directory (default: data)"
    )
    parser.add_argument(
        "-m",
        "--month",
        type=str,
        required=True,
        help="Month to process, e.g Jan"
    )

    parser.add_argument(
        "-s",
        "--station",
        type=arg_int_or_str,
        required=True,
        help="Station code or name, e.g. 254180090 is Gdańsk-Rębiechowo, https://klimat.imgw.pl/pl/meta-dane/"
    )

    return parser.parse_args()


def prepare_stations_data() -> pd.DataFrame:
    """
    Prepare stations data (including station code, name) based on IMGW WFS service

    :return: data frame with stations
    """
    print("Preparing stations data...")
    print("Fetching data from IMGW WFS...")
    data = gpd.read_file(
        filename=IMGW_STATIONS_WFS,
        columns=["name"],
        ignore_geometry=True
    )
    print("Data fetched.")
    print("Extracting station code, station name...")
    data[["station_code", "station_name"]] = pd.DataFrame(data["name"].tolist()).iloc[:, :2]
    data["station_name"] = data["station_name"].str.upper()
    data.drop(columns=["name"], inplace=True)
    print("Stations data prepared.")
    return data


def get_station_code(station_name: str) -> int | None:
    """
    Return station code (numeric).

    :param station_name: station name for which code should be extracted
    """
    stations = prepare_stations_data()
    station_code = stations.loc[stations["station_name"] == station_name.upper(), "station_code"].item()
    if not station_code:
        print(f"Station code not found for station name {station_name}")
        sys.exit(1)

    return int(station_code)



def filter_files(data_dir: Path,
                 month: list[int]) -> list[Path]:
    """
    Return filest to be processed.

    :param data_dir: path to data temp data fetched from IMGW
    :param month: month to process, e.g Jan
    :return: list of paths to files for given month
    """
    result = []
    for file in data_dir.rglob("*.zip"):
        _, file_month, *_ = file.stem.split("_")
        file_month = int(file_month)
        if file_month == month:
            result.append(file)

    return result



def get_station_data(file: Path,
                     station_code: int) -> pd.DataFrame:
    """
    Return temp data for given station.

    :param file: path to data temp data fetched from IMGW
    :param station_code: station to be processed
    :return: dataframe with temp for given month and station
    """
    print(f"Reading {file}")
    df = pd.read_csv(file,
                     usecols=[0, 1, 2, 3, 4, 5, 6],
                     names=[
                         "code",
                         "name",
                         "year",
                         "month",
                         "day",
                         "hour",
                         "temp"
                     ],
                     encoding="ANSI")
    return df[df["code"] == station_code]


def main() -> None:
    # Note:
    # As GeoPandas/Pandas exercise  WFS service is used to find station code based on station name instead of using
    # 'name' column in CSV data files
    args = parse_args()
    try:
        month = MONTHS[args.month.upper()]
    except KeyError:
        print("Invalid month")
        sys.exit(1)

    station_code = None
    match args.station:
        case str(): station_code = get_station_code(args.station)
        case int(): station_code = args.station

    data_temp_month = pd.DataFrame()
    files = filter_files(args.data_dir, month)
    for file in files:
        data = get_station_data(file, station_code)
        temp_day_avg = data.groupby(["day"])["temp"].mean().round(1)
        year = file.stem.split("_")[0]
        data_temp_month[year] = temp_day_avg

    output = f"{args.station}_{args.month}.csv"
    data_temp_month.to_csv(output, index=False)
    print(f"Result saved to {output}")

if __name__ == "__main__":
    main()
