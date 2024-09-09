from pathlib import Path

import rioxarray
import xarray as xr

from definitions import DATA_PATH


def main(modis_file: str | Path) -> tuple[list, list]:
    """
    Split one big MODIS datasets into smaller ones based on date
    """
    modis_dataset = xr.open_dataset(modis_file, decode_coords="all")
    dates, modis_datasets = zip(*modis_dataset.groupby("time"))
    modis_dataset.close()
    return dates, modis_datasets


if __name__ == "__main__":
    out_dir = DATA_PATH / "modis_ndvi"
    out_dir.mkdir(exist_ok=True)

    modis_file = sorted((DATA_PATH / "MODIS NDVI").glob("MOD13Q1*.nc"))[0]
    dates, modis_datasets = main(modis_file=modis_file)

    paths = [
        out_dir / f"{modis_file.stem}_{date.strftime('%Y%m%d')}.nc" for date in dates
    ]

    xr.save_mfdataset(datasets=modis_datasets, paths=paths)
