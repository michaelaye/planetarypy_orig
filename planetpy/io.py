import toml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

configpath = Path.home() / ".planetpy.toml"


def print_error():
    print("No configuration file {} found.\n".format(configpath))
    print(
        """Please run `planetpy.io.set_database_path()` and provide the path where
you want to archive your downloaded data."""
    )
    print(
        f"`planetpy` will store this path in {configpath}, where you can easily change it later."
        " Note, that it will be stored with a host-name, that way you can have different archiving"
        " paths on different machines, but still share the same config file."
    )


if not configpath.exists():
    print_error()
else:
    config = toml.load(str(configpath))
    if len(config) == 0:
        print(
            "Config file has no data storage path."
            "Please run io.set_database_path(folder) with `folder` pointing to the directory "
            "where you want data to be stored."
        )
    try:
        rootpath = Path(config["data_archive"]["path"])
    except KeyError:
        raise KeyError("data_archive/path key not found in config.")


def set_database_path(dbfolder):
    """Use to write the database path into the config.

    Parameters
    ----------
    dbfolder : str or pathlib.Path
        Path to where planetpy will store data it downloads..
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
