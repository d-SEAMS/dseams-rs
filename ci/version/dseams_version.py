import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
with (ROOT / "Cargo.toml").open("rb") as stream:
    VERSION = tomllib.load(stream)["workspace"]["package"]["version"]
