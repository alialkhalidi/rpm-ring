from re import split
import csv
from os import environ, path
import sys
import logging
import argparse

# expression does not cover distro and epoch, for example el7 and 8 in package-8:1.2.3-4.el7.x86_64.rpm
rpm_pkg_name_tokenizer_re = r"^(?P<name>.+)-(?P<version>\d+\.\d+\.\d+(?:\.\d+){,2})(?P<release>-.*)?\.(?P<arch>\w+)\.(?P<fext>rpm)$"
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))) + "/src")

logger: logging.Logger = logging.getLogger(__name__)
logging.basicConfig()

logger.setLevel(environ.get("LOG_LEVEL", "INFO").upper())

parser = argparse.ArgumentParser(
    description="RPN Ring", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    "--csvFile",
    type=str,
    required=False,
    help="Hammer-cli csv export of the form id,rpm. Or specify via CSV_FILE envrionment variable",
)
parser.add_argument(
    "--keepVersions",
    type=int,
    required=False,
    default="5",
    help="Number of versions to keep",
)
parser.add_argument(
    "--versionReleases",
    type=int,
    required=False,
    default="1",
    help="Per version snapshot or release to keep",
)
args = parser.parse_args()


# read these from the command parameter as optional of from the environment
versions_to_keep = args.keepVersions
releases_per_version_to_keep = args.versionReleases

logger.debug(f"versions_to_keep: {versions_to_keep}")
logger.debug(f"releases_per_version_to_keep: {releases_per_version_to_keep}")


def rpm_name_parser(pkg_name: str) -> tuple:
    """Parse name to tokens

    Parses an rpm file name of the form: name-version[-release].architecture.rpm into tokens and returns tuple.
    """
    tokens = [
        token for token in split(rpm_pkg_name_tokenizer_re, pkg_name) if token != ""
    ]
    if len(tokens) < 5:
        logger.error(f"error parsing package {pkg_name}")
        return None
    if tokens[2]:
        tokens[2] = tokens[2].lstrip("-")
    return tuple(tokens)


def load_csv_file(filename: str) -> dict:
    """Load CSV data from file

    Loads data from a csv data file created with hammer into a dictionary. Expects entries to be unique.
    example: unique-id,rpm-name
    """
    data = dict()
    try:
        with open(filename, "r") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                data[row[0]] = row[1]
    except Exception as e:
        logger.error(f"Error opening file: {e}")
        exit(1)
    return data


def process_rpm_data(rpm_data: dict) -> dict:
    """Create dict of rpm data

    From a dict of rpms(id,name), return a dict of rpms with following structure.
    rpm[name]:
        version:
            releases:
                ids: []
                names: []
            ids: []
    """
    logger.debug(f"process_rpm_data start. rpm_data {rpm_data}")
    if not rpm_data:
        logger.warning("got empty params")
        return None
    rpms = dict()
    for id, rpm in rpm_data.items():
        rpm_parts = rpm_name_parser(rpm)
        if not rpm_parts:
            logger.debug(f"omitting package {rpm}")
            continue
        # (name, version, release, arch, rpm)
        n = rpm_parts[0]
        v = rpm_parts[1]
        r = rpm_parts[2]
        if not rpms.get(n):
            logger.debug(f"name Not in list. rpm name {n} version {v} release {r}")
            rpms[n] = {v: {"releases": {"ids": [], "names": []}, "ids": []}}
        else:
            logger.debug(f"name In list. rpm name {n} version {v} release {r}")
            if not rpms[n].get(v):
                logger.debug(
                    f"version not in list. rpm name {n} version {v} release {r}"
                )
                rpms[n].update({v: {"releases": {"ids": [], "names": []}, "ids": []}})

        if r not in ["1"]:  # snapshot-release
            rpms[n][v]["releases"]["ids"].append(id)
            rpms[n][v]["releases"]["names"].append(r)
        else:
            rpms[n][v]["ids"].append(id)

    logger.debug(f"process_rpm_data end. rpm_data {rpms}")
    return rpms


def get_retired_ids(rpm_data: dict) -> list:
    """Create a list of retired rpm ids

    From a dict of rpms(id,name), return the list of ids to retire or delete.
    rpm[name]:
        version:
            releases:
                ids: []
                names: []
            ids: []
    """
    logger.debug(f"get_retired_ids start. rpm_data {rpm_data}")
    if not rpm_data:
        logger.warning("got empty params")
        return None

    rpms = process_rpm_data(rpm_data)
    if not rpms:
        logger.warning("got empty rpm processed data")
        return None
    global_retire_list = list()
    version_retire_list = list()
    release_retire_list = list()
    for rpm in rpms.keys():
        # sort the versions
        versions = [k for k in list(rpms[rpm].keys())[::-1]]
        retired_versions = versions[versions_to_keep:]
        remaining_versions = versions[:versions_to_keep]
        for v in retired_versions:
            d = rpms[rpm][v]
            version_retire_list.append(d.get("ids"))
            version_retire_list.append(d["releases"].get("ids"))

        for v in remaining_versions:
            r = rpms[rpm][v]["releases"].get("ids")
            r.sort(reverse=True)
            release_retire_list.append(r[releases_per_version_to_keep:])
            # remove duplicate versions
            d = rpms[rpm][v]["ids"]
            d.sort()
            version_retire_list.append(d[1:])

    logger.debug(f"version ids to retrire: {version_retire_list}")
    logger.debug(f"release ids to retrire: {release_retire_list}")
    global_retire_list = version_retire_list + release_retire_list
    logger.debug(f"global ids to retrire: {global_retire_list}")

    return global_retire_list


def flatten(ll):
    return [x for l in ll for x in l]


def main():
    # when CSV_FILE is set, ignore parameter
    input_file = environ.get("CSV_FILE")
    if not input_file:
        logger.debug(
            "CSV_FILE environment variable not set, processing input arguments instead"
        )
        input_file = args.csvFile

    logger.debug(f"processing {input_file}")
    rpm_data = load_csv_file(input_file)
    ids = flatten(get_retired_ids(rpm_data))
    if ids is None:
        logger.warning("should get empty list but not None ids object")
        sys.exit(1)
    if len(ids) == 0:
        logger.debug("no packages to retire")
    else:
        logger.debug(f"{len(ids)} packages to retire")
        if logger.isEnabledFor(logging.DEBUG):
            for id in ids:
                logger.debug(f"package {rpm_data.get(id)} will be retired")

    print(",".join(ids))
    return ",".join(ids)


if __name__ == "__main__":
    main()
