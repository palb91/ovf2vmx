#!/usr/bin/env python3
#
# Copyright (C) 2016 Pierre-Alberic TROUPLIN

"""
VMX to OVF VMWare virtual machines converter.

Usage:
    vmx2ovf [-h] [-v] [-d DEST] [-z | -Z] FILE...

Options:
    -h, --help              Print this help.
    -d, --destination DEST  Use DEST as destination folder.
                            Default: _converted
    -z, --zip               Create a zip archive.
    -Z, --zip-only          Create a zip archive and remove not zipped content.
    -v, --version           Print the version.

Arguments:
    FILE                    File to convert (must be .vmx).
"""

import os
import sys
import zipfile
from datetime import datetime
from subprocess import Popen
from hashlib import sha1
from docopt import docopt


class ConvertException(Exception):
    """
        Handle convertion exception with ovftool.
    """
    pass


def get_ovftool_path():
    """
        Verify ovftool is installed and return its absolute path.
    """
    ovftool_path = "C:\Program Files (x86)\VMware"
    for root, dirs, files in os.walk(ovftool_path):
        for file in files:
            if file.endswith("ovftool.exe"):
                return os.path.join(root, file)

    raise FileNotFoundException("ovftool.exe")


def edit_ovf_file(ovf_path):
    """
        Modify VMX version into OVF file (Compatibility reason).
    """
    with open(ovf_path, "r") as f:
        ovf = f.readlines()

    for n, line in enumerate(ovf):
        if "VirtualSystemType" in line:
            ovf[n] = ("        <vssd:VirtualSystemType>vmx-8" +
                      "</vssd:VirtualSystemType>\n")
            break

    with open(ovf_path, "w") as f:
        f.writelines(ovf)

    print(" [+] OVF modified.")


def edit_mf_file(ovf_path, mf_path):
    """
        Get the OVF SHA1 and add it into the MF file.
    """
    # Get OVF SHA1
    with open(ovf_path, "rb") as f:
        ovf = f.read()

    ovf_sha1 = sha1()
    ovf_sha1.update(ovf)

    # Modify MF with new OVF SHA1
    with open(mf_path, "r") as f:
        mf = f.readlines()

    ovf_line = mf[0].split("= ")[0]
    mf[0] = "= ".join([ovf_line, ovf_sha1.hexdigest()]) + "\n"

    with open(mf_path, "w") as f:
        f.writelines(mf)

    print(" [+] MF modified.")


def convert(vmx_path, vm_name, dest_path):
    """
        Converts a VM from VMX to OVF using ovftool.
    """
    print("    ----- Start ovftool -----")
    p = Popen([get_ovftool_path(), "--name=" + vm_name, vmx_path, dest_path])

    convert_return = p.wait()
    print("    ----- Stop ovftool -----\n")

    if convert_return == 1:
        raise ConvertException(" [-] VM convertion failed for: " + vmx_path)

    print(" [+] VM converted.")

    conv_path = os.path.join(dest_path, vm_name)

    ovf_path = os.path.join(conv_path, vm_name + ".ovf")
    mf_path = os.path.join(conv_path, vm_name + ".mf")

    edit_ovf_file(ovf_path)
    edit_mf_file(ovf_path, mf_path)


def zip_result(dest_path, vm_name, delete):
    """
        Create a zip archive of provided VM.
    """
    def get_files(path_to_browse):
        """Return an arraylist containing files into folder."""
        list_files = []
        for f in os.listdir(path_to_browse):
            list_files.append(f)
        return list_files

    def delete_path(path_to_browse):
        """delete all files into provided path and path itself."""
        print(" [+] Removing files.")
        for f in get_files(path_to_browse):
            os.remove(os.path.join(path_to_browse, f))
            print("     > %s removed" % f)
        os.rmdir(path_to_browse)
        print(" [+] Files removed.")

    abs_path = os.path.join(dest_path, vm_name)
    zip_path = abs_path + ".zip"

    # Create zip archive
    z = zipfile.ZipFile(zip_path, mode="w")
    print(" [+] Creating zip file.")

    for f in get_files(abs_path):
        z.write(os.path.join(abs_path, f), os.path.join(vm_name, f))
        print("     > %s added to zip file." % f)

    z.close()
    print(" [+] Zip file Created.")

    # Delete files if requested
    if delete:
        delete_path(abs_path)


def create_dest(dest_path):
    """
        Create the destination folder for converted VM.
        Default: ./_converted
    """
    try:
        os.mkdir(dest_path)
        print("\n [+] Path '%s' created.\n" % dest_path)
    except FileExistsError:
        print("\n [!] Path '%s' already exists, will be used.\n" % dest_path)
        pass


def is_vmx(vm):
    """
        Valid a content as a .vmx file.
    """
    if vm.split(".")[-1] != "vmx":
        print(" [-] %s is not a .vmx file\n" % vm)
        return False

    return True


def get_vm_name(vmx_path, dest_path, *, _ts=None):
    """
        Return the final_name of the VM.
    """
    vm_name = ".".join(os.path.split(vmx_path)[1].split(".")[:-1])
    new_vm_name = vm_name

    if os.path.exists(os.path.join(dest_path, vm_name)):
        if not _ts:
            _ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        new_vm_name += "_" + _ts

    return vm_name, new_vm_name


def main():
    # Get arguments
    args = docopt(__doc__, version="0.4")
    dest_path = args["--destination"] or "_converted"
    delete    = args["--zip-only"]
    zippable  = args["--zip"]         or delete
    vm_queue  = args["FILE"]

    # Create folder for converted VMs
    create_dest(dest_path)

    # Convert VMs
    for vm in vm_queue:
        print("==========  Start VM: %s  ==========" % vm)

        if not is_vmx(vm):
            continue

        vmx_path = os.path.abspath(os.path.expanduser(vm))
        ori_vm_name, vm_name = get_vm_name(vmx_path, dest_path)

        try:
            convert(vmx_path, vm_name, dest_path.replace(vm_name, ori_vm_name))

            if zippable:
                zip_result(dest_path, vm_name, delete)

        except Exception as e:
            print(e, "\n")
            continue

        print()


if __name__ == '__main__':
    main()
