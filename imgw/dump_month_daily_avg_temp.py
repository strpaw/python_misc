"""Script to dump temperature data (daily average) for given month and station.

Example usage, dump data for Gdańsk Rębiechowo (station code 254180090, May for data downloaded from
https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/terminowe/klimat (yests 2001-2025)
into dir imgw_data

python .\dump_month_daily_avg_temp.py -d imgw_data -m May -s 254180090
"""
import argparse
from pathlib import Path
import sys

import pandas as pd


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
        type=int,
        required=True,
        help="Station code, e.g. 254180090 is Gdańsk-Rębiechowo, https://klimat.imgw.pl/pl/meta-dane/"
    )

    return parser.parse_args()


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
    args = parse_args()
    try:
        month = MONTHS[args.month.upper()]
    except KeyError:
        print("Invalid month")
        sys.exit(1)

    data_temp_month = pd.DataFrame()
    files = filter_files(args.data_dir, month)
    for file in files:
        data = get_station_data(file, args.station)
        temp_day_avg = data.groupby(["day"])["temp"].mean().round(1)
        year = file.stem.split("_")[0]
        data_temp_month[year] = temp_day_avg

    output = f"{args.station}_{args.month}.csv"
    data_temp_month.to_csv(output, index=False)
    print(f"Result saved to {output}")

if __name__ == "__main__":
    main()
