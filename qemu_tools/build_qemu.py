#!/usr/bin/env python3

import os
import argparse
import subprocess
from collections import namedtuple


def main():
    args = parse_args()

    starting_dir = os.getcwd()
    try:
        build_qemu(args.qemu_source_dir)
    except QemuInstallerError as e:
        print("ERROR: " + str(e))
        os.chdir(starting_dir)
        exit(-1)


class QemuInstallerError(Exception):
    pass


Version = namedtuple("Version", "major minor micro")

def get_qemu_version(source_dir):
    version_filepath = os.path.join(source_dir, "VERSION")
    if not os.path.isfile(version_filepath):
        raise QemuInstallerError("Missing VERSION file")

    with open(version_filepath, "r") as f:
        version_string = f.readline()

    version_parts = version_string.split(".")
    return Version(int(version_parts[0]),
                   int(version_parts[1]),
                   int(version_parts[2]))


def run(command=[], error_message="", cwd="."):
    try:
        res = subprocess.run(command,
                             env=os.environ, check=True,
                             cwd=cwd)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise QemuInstallerError(error_message + str(e))


def build_qemu(source_dir):
    version = get_qemu_version(source_dir)
    # major version match is probably good enough,
    # deps don't change that fast.
    if version.major == 2:
        dockerfile = "dockerfile_2.5.0"
    elif version.major == 4:
        dockerfile = "dockerfile_4.2.1"
    else:
        raise QemuInstallerError("unexpected Qemu version: %d.%d.%d" % version)

    script_dir = os.path.split(os.path.realpath(__file__))[0]
    target_tar = os.path.join(script_dir, "docker_builder", "qemu_src_" + str(version.major) + ".tar")
    run(command=["./scripts/archive-source.sh", target_tar],
        error_message="Tarring qemu source failed: ",
        cwd=source_dir)

    run(command=["sudo", "docker", "build", "-t", "qemu_build",
                 "-f", "docker_builder/" + dockerfile,
                 "docker_builder"],
        error_message="sudo docker build failed: ")

    try:
        run(command=["sudo", "docker", "rm", "qemu_build_output"],
            error_message="sudo docker rm failed: ")
    except QemuInstallerError:
        # It's fine if this fails due to the image not existing
        # on first attempt
        pass

    run(command=["sudo", "docker", "create", "--name", "qemu_build_output",
                 "qemu_build"],
        error_message="sudo docker create failed: ")

    run(command=["sudo", "docker", "cp", "qemu_build_output:/home/ml_builder/qemu_" +
                 str(version.major) + ".zip",
                 "."],
        error_message="sudo docker cp failed: ")


def parse_args():
    description = """
    Script to build Qemu with EOS support, using Docker.
    The Qemu binaries are created as qemu.zip.
    """

    script_dir = os.path.split(os.path.realpath(__file__))[0]
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("-s", "--qemu_source_dir",
                        default=os.path.realpath(os.path.join(script_dir,
                                                              "..", "..", "qemu-eos")),
                        help="source dir for ML Qemu, default: %(default)s")

    args = parser.parse_args()

    try:
        if not os.path.isdir(args.qemu_source_dir):
            raise QemuInstallerError("Qemu source dir didn't exist.  "
                                     "You may need to clone the qemu-eos repo.")
        if not os.path.isdir(os.path.join(args.qemu_source_dir,
                                          ".git")):
            raise QemuInstallerError("Qemu source dir didn't look like a git repo.  "
                                     "It should contain the qemu-eos repo.")
    except QemuInstallerError as e:
        print("ERROR: " + str(e))
        exit(-1)

    return args


if __name__ == "__main__":
    main()
