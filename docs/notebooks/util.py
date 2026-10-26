import shutil
import time
import urllib.request
import zipfile
from os import PathLike
from pathlib import Path


def get_dataset(
    save_fp: str | PathLike = "NHS.gdb",
    url="https://hepgis-usdot.hub.arcgis.com/api/download/v1/items/dce9f09392eb474c8ad8e6a78416279b/filegdb?layers=0",
) -> str:
    save_fp = Path(save_fp)
    if save_fp.exists():
        print("Done! The .gdb already exists")
        return save_fp.absolute().as_posix()
    zip_fp = save_fp.with_suffix(".zip")

    print(f"Downloading from {url}...")
    req = urllib.request.Request(url)
    while True:
        with urllib.request.urlopen(req) as response, open(zip_fp, "wb") as f:
            if str(response).startswith(
                '{"message":"Up to date download file is being generated'
            ):
                print("Retrying...")
                time.sleep(10)
            else:
                shutil.copyfileobj(response, f)
                break

    print(f"Extracting zip archive to {save_fp}...")
    with zipfile.ZipFile(zip_fp, "r") as zip_ref:
        zip_ref.extractall(save_fp.parent)

    zip_fp.unlink()

    extracted_gdbs = list(save_fp.parent.rglob("*.gdb"))

    if extracted_gdbs:
        original_gdb = extracted_gdbs[0]
        original_gdb.rename(save_fp)
        print("Done!")
        return save_fp.absolute().as_posix()
    else:
        raise FileNotFoundError(
            "Error: No .gdb folder found inside the extracted archive."
        )


class Timer:
    def __init__(self) -> None:
        self.start_time = 0
        self.end_time = 0

    def start(self) -> None:
        self.start_time = time.time()

    def stop(self) -> None:
        self.end_time = time.time()
        result = round(self.end_time - self.start_time, 4)
        if result > 0.0:
            print(f"{result} seconds")
        else:
            print("< 10 ms")
