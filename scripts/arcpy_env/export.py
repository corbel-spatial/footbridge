import subprocess
import sys
from pathlib import Path
from shutil import rmtree


def main() -> None:
    if not sys.platform.startswith("win"):
        print("This script requires Windows")
        sys.exit(1)

    out_dir = Path(__file__).resolve().parent
    print(out_dir)

    commands = (
        ["pixi", "init"],
        [
            "pixi",
            "import",
            "-e",
            "default",
            "--format",
            "conda-env",
            r"C:\Program Files\ArcGIS\Pro\bin\Python\res\environment.yaml",
        ]
    )

    for args in commands:
        print(">", " ".join(args))
        result = subprocess.run(args=args, cwd=out_dir, shell=False)
        print(result.stderr)

    with open(out_dir / "pixi.toml", "r") as f:
        toml = f.readlines()

    with open(out_dir / "pixi.toml", "w") as f:
        for line in toml:
            vers = line.split("= {")
            if len(vers) == 1:
                f.write(vers[0])
            else:
                f.write(vers[0] + '= "*"\n' )

if __name__ == "__main__":
    main()
