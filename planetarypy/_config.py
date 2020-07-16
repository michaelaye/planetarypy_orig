import logging
from pathlib import Path

import toml

logger = logging.getLogger(__name__)

# create configpath depending on package name
pkg_name = __name__.split(".")[0]
configpath = Path.home() / f".{pkg_name}.toml"


def print_error():
    print("No configuration file {} found.\n".format(configpath))
    print(
        """Please run `planetarypy.set_database_path()` and provide the path where
you want to archive your downloaded data."""
    )
    print(
        f"`planetarypy` will store this path in {configpath}, where you can easily change it later."
        " Note, that it will be stored with a host-name, that way you can have different archiving"
        " paths on different machines, but still share the same config file."
    )


def set_database_path(dbfolder):
    """Use to write the database path into the config.

    Parameters
    ----------
    dbfolder : str or pathlib.Path
        Path to where planetarypy will store data it downloads..
    """
    # First check if there's a config file, so that we don't overwrite
    # anything:
    try:
        config = toml.load(str(configpath))
    except IOError:  # config file doesn't exist
        config = {}  # create new config dictionary

    # check if there's an `data_archive` sub-dic
    try:
        archive_config = config["data_archive"]
    except KeyError:
        config["data_archive"] = {"path": dbfolder}
    else:
        archive_config["path"] = dbfolder

    with open(configpath, "w") as f:
        ret = toml.dump(config, f)
    print(f"Saved database path {ret} into {configpath}.")


def get_data_root():
    config = toml.load(str(configpath))
    data_root = Path(config["data_archive"]["path"]).expanduser()
    data_root.mkdir(exist_ok=True, parents=True)
    return data_root


if not configpath.exists():
    print(f"No configuration file {configpath} found.\n")
    savepath = input(
        "Provide the path where all planetarypy-managed data should be stored:"
    )
    set_database_path(savepath)

data_root = get_data_root()
config = toml.load(str(configpath))
