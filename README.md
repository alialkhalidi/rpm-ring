# rpm-ring
rpm ring buffer to maintain last X versions (and Y release per version).

Helps trim-down package storage by maintaining only the most recent and relevant packages in an RPM repository, like Foreman.

## Quick Start
The utility operates on a comma-seperated input file. Currently, hammer-cli is used to generate such a file, with following fields:
Id, rpm-package-name

Sample command to generate the export:
```bash
$ hammer --username USERNAME --password PASSWORD --server https://FOREMAN_SERVER  --output csv package list --repository-id REPO_ID --fields Id,Filename
```

## Usage
```bash
usage: rpm-ring [-h] --csvFile CSVFILE [--keepVersions KEEPVERSIONS] [--versionReleases VERSIONRELEASES]

RPM Ring

options:
  -h, --help            show this help message and exit
  --csvFile CSVFILE     Hammer-cli csv export of the form id,rpm (default: None)
  --keepVersions KEEPVERSIONS
                        Number of versions to keep (default: 5)
  --versionReleases VERSIONRELEASES
                        Per version snapshot or release to keep (default: 1)
```

