#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil
import tarfile
from enum import Enum
from typing import Final
from pathlib import Path

USAGE_STR: Final[str] = """Usage: run_test.py [options]

options:
    --after-clean    Clean files after test.
"""


def load_test_versions() -> list[str]:
    version_file = open("test_versions.txt", "r")
    try:
        lines = version_file.readlines()
        for i in range(0, len(lines)):
            lines[i] = lines[i].strip(" \r\n")

        return lines
    finally:
        version_file.close()


def run_cmd(cmd: str, fail_str: str | None = None, *, timeout: float | None = None) -> None:
    print("* Running command: " + cmd)

    result: Final = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)

    print("\n*- Command output:")
    print(result.stdout.decode())
    print("*- Command error output:")
    print(result.stderr.decode())
    print(f"*- Command return code: {result.returncode}")

    if result.returncode != 0:
        if fail_str is None:
            print("* Process failed.")
        else:
            print(f"* {fail_str} failed.")

        exit(result.returncode)


class SystemType(Enum):
    WINDOWS = "Windows",
    LINUX = "Linux",
    MACOS = "MacOS",
    UNKNOW = "Unknow"

    @staticmethod
    def get_current_os():
        if sys.platform.startswith('linux'):
            return SystemType.LINUX
        elif sys.platform.startswith('win'):
            return SystemType.WINDOWS
        elif sys.platform.startswith('darwin'):
            return SystemType.MACOS

        return SystemType.UNKNOW


def main(argv: list[str]) -> int:
    argc: int = len(argv)

    # Phase args
    after_clean: bool = False
    if argc == 1:
        pass
    elif argc == 2:
        if argv[0] == "--after-clean":
            after_clean = True
        else:
            print(USAGE_STR)
            return 1
    else:
        print(USAGE_STR)
        return 1

    print(f"After clean: {after_clean}")

    current_os: Final = SystemType.get_current_os()
    print(f"Detected current operating system is \"{current_os}\"")

    project_source_dir: Final = Path(os.path.abspath(os.getcwd()))
    print(f"Working directory is {project_source_dir}")

    test_versions: Final = load_test_versions()
    print(f"Will running test on versions: {test_versions}")

    # Download
    print("Downloading...")
    for version in test_versions:
        if Path(f"lua-{version}.tar.gz").exists():
            print(f"Source for version {version} already exists, skip downloading.")
        else:
            run_cmd(f"curl https://www.lua.org/ftp/lua-{version}.tar.gz -o lua-{version}.tar.gz",
                    "Download source",
                    timeout=300,
                    )

        if Path(f"lua-{version}-tests.tar.gz").exists():
            print(f"Test for version {version} already exists, skip downloading.")
        else:
            run_cmd(f"curl https://www.lua.org/tests/lua-{version}-tests.tar.gz -o lua-{version}-tests.tar.gz",
                    "Download tests",
                    timeout=300,
                    )

    print("--- Done.")

    # Unpack
    print("--- Unpacking...")
    for version in test_versions:
        print(f"--- >>> Unpacking file lua-{version}.tar.gz")
        with tarfile.open(f"lua-{version}.tar.gz", "r:gz") as tar:
            tar.extractall(filter="data")
        print("--- >>> Done.")

        print(f"--- >>> Unpacking file lua-{version}-tests.tar.gz")
        with tarfile.open(f"lua-{version}-tests.tar.gz", "r:gz") as tar:
            tar.extractall(filter="data")
        print("--- >>> Done.")

        print(f"--- >>> Copying files from lua-{version}-tests/ to lua-{version}/src/test/")
        shutil.copytree(src=f"lua-{version}-tests/",
                        dst=f"lua-{version}/src/test/",
                        )
        print("--- >>> Done.")

    print("--- Done.")

    # Run test
    platform_feature_command: str = "-DLUA_USE_PLATFORM_FEATURES="
    if current_os == SystemType.LINUX:
        platform_feature_command += "\"LINUX\""
    elif current_os == SystemType.MACOS:
        platform_feature_command += "\"MACOSX\""
    else:
        platform_feature_command += "\"\""

    multi_config_on_build_cmd: str = ""
    multi_config_on_ctest_cmd: str = ""
    if current_os == SystemType.WINDOWS:  # Use MSVC
        multi_config_on_build_cmd = "--config Release"
        multi_config_on_ctest_cmd = "-C Release"

    print("========================================================")
    print(f"platform_feature_command = {platform_feature_command}")
    print(f"multi_config_on_build_cmd = {multi_config_on_build_cmd}")
    print(f"multi_config_on_ctest_cmd = {multi_config_on_ctest_cmd}")
    print()

    for version in test_versions:
        print(f"+ Testing version: {version}")
        dir_name = f"lua-{version}"
        source_dir = project_source_dir / dir_name / "src"

        print(f"dir_name = {dir_name}")
        print(f"source_dir = {source_dir}", end="\n\n")

        # Config
        run_cmd(
            f"cmake -S {project_source_dir} -B build-{dir_name} "
            f"-DLUA_SOURCE_DIRECTORY:PATH={source_dir} "
            f"{platform_feature_command} "
            "-DLUA_ENABLE_TESTS:BOOL=ON -DCMAKE_BUILD_TYPE=Release "
            "--debug-output",
            "Config",
        )

        # Build
        run_cmd(
            f"cmake --build build-{dir_name} {multi_config_on_build_cmd} "
            "--verbose",
            "Build",
        )

        # Run test
        run_cmd(
            f"cd build-{dir_name} && ctest . {multi_config_on_ctest_cmd} "
            "--verbose",
            "Run test",
        )

        # Clean
        if after_clean:
            print("Clean...")
            os.rmdir(f"build-{dir_name}")
            os.rmdir(dir_name)
            os.remove(f"lua-{version}.tar.gz")
            print("--- Done.")

        print(f"+- Version {version} test passed.", end="\n\n")

        print("------------------------------------------------")

    print("\n        All test(s) passed!")

    return 0


if __name__ == "__main__":
    exit(main(sys.argv))
