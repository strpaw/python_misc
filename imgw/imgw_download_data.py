"""Script to download public data with temperature from IMGW (Instytut Meteorologii i Gospodarki Wodnej,
Institute of Meteorology and Water Management)"""
import requests

from imgw_common import (
    MONTH_RANGE,
    load_config
)


if __name__ == "__main__":
    config = load_config()
    config.data_dir.mkdir(exist_ok=True)
    for year in range(config.range.from_year, config.range.to_year + 1):
        for month in MONTH_RANGE:
            fname = f"{year}_{month:02d}_k.zip"
            print(f"Downloading file {fname}...")
            response = requests.get(f"{config.data_base_url}/{year}/{fname}",
                                    stream=True,
                                    timeout=30)
            with open(config.data_dir / fname, "wb") as f:
                f.write(response.content)
            print(f"Downloading file {fname} completed.")
