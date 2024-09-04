import rioxarray
import xarray as xr
from tqdm import tqdm

from definitions import DATA_PATH


def compute_group_anomaly(group: xr.Dataset) -> xr.Dataset:
    """
    Helper function for computing the anomaly
    """
    group_mean = group.mean(dim="time")
    anomaly = group - group_mean
    return anomaly


def anomaly_all(month: int) -> None:
    """
    Compute the anomaly dataset
    """
    files = sorted((DATA_PATH / "ERA5D-Land").glob(f"*_{str(month).zfill(2)}_DA.nc"))

    months_dataset = xr.open_mfdataset(files)
    # Using groupby we do not need to program the ad hoc case for February 29th,
    # xarray's groupby backend handles it for us
    anomaly_dataset = months_dataset.groupby("time.dayofyear").apply(
        compute_group_anomaly
    )
    months_dataset.close()
    return anomaly_dataset


if __name__ == "__main__":
    out_dir = DATA_PATH / "anomaly_all"
    out_dir.mkdir(exist_ok=True)

    for month in tqdm(range(1, 12 + 1), desc="Computing and saving anomalies"):
        anomaly_dataset = anomaly_all(month=month)
        years, anomaly_datasets = zip(*anomaly_dataset.groupby("time.year"))
        paths = [
            out_dir / f"era5_land_{year}_{str(month).zfill(2)}_AnoAll.nc"
            for year in years
        ]

        if not paths[0].exists():
            xr.save_mfdataset(datasets=anomaly_datasets, paths=paths)

        anomaly_dataset.close()
