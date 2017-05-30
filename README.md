
# ovf2vmx
VMX to OVF virtual machines converter. (ovftool wrapper)
I created this tool to make conversion easier for old ESX versions.

## Usage:
    vmx2ovf [-h] [-v] [-d DEST] [-z | -Z] FILE...

## Options:
    -h, --help              Print this help.
    -d, --destination DEST  Use DEST as destination folder.
                            Default: _converted
    -z, --zip               Create a zip archive.
    -Z, --zip-only          Create a zip archive and remove not zipped content.
    -v, --version           Print the version.

## Arguments:
    FILE                    File te convert (must be .vmx).
