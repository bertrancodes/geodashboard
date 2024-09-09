from pathlib import Path
from zipfile import ZipFile

from tqdm import tqdm

from definitions import DATA_PATH


def main(file: str | Path) -> None:
    """Extract and rename ERA5-Land zip files"""
    out_dir = DATA_PATH / "ERA5-Land"
    with ZipFile(file=file, mode="r") as f:
        compressed_name = f.namelist()[0]
        f.extractall(path=out_dir)

    out_file = out_dir / compressed_name
    out_file.rename(out_file.with_stem(file.stem.split(".")[0]))


if __name__ == "__main__":
    files = sorted((DATA_PATH / "ERA5-Land (zip)").glob("*.netcdf.zip"))

    for file in tqdm(files, desc="Extracting and renaming files"):
        main(file=file)
