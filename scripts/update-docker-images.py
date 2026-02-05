#! /usr/bin/env python

import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_dir = Path(__file__).parent
repo_root_path = (_dir / "..").resolve()


ANSI_GREEN = "\033[0;32m"
ANSI_RED = "\033[0;31m"
ANSI_RESET = "\033[0m"


@dataclass(frozen=True)
class DockerImage:
    name: str
    tag: str
    digest: str

    @property
    def sha(self) -> str:
        return self.digest.split(":", maxsplit=2)[1]


class Globals:
    made_changes = False


def docker_image_with_digest_specifier(image: DockerImage) -> str:
    return f"{image.name}:{image.tag}@{image.digest}"


@lru_cache
def get_latest_docker_image(image_name: str, tag: str) -> DockerImage:
    output = subprocess.check_output(f"docker pull {image_name}:{tag}", shell=True, text=True)
    for line in output.splitlines():
        if line.startswith("Digest:"):
            sha = line.split(maxsplit=2)[1]
            return DockerImage(image_name, tag, sha)
    raise RuntimeError(f"Could not find the digest for Docker image {image_name}:{tag}")


def update_docker_file(prefix: str, path: Path, skip_images: list[str]):
    lines = path.read_text().splitlines(keepends=False)
    has_changes = False
    regex = re.compile(
        r"^(?P<indent> *)"
        + prefix
        + r" +(?P<image>[^ :@]+):(?P<tag>[^@]*)(?P<digest>@sha256:(?P<sha>[a-f0-9]+))?(?P<eol>.*)$"
    )

    for i, line in enumerate(lines):
        m = regex.match(line)

        if not m:
            continue

        indent = m.group("indent")
        image_name = m.group("image")
        tag = m.group("tag")
        sha = m.group("sha")
        eol = m.group("eol")

        if image_name in skip_images:
            continue

        if tag is None:
            continue

        if sha is None:
            sha_str = "None"

        image = get_latest_docker_image(image_name, tag)

        if sha != image.sha:
            new_line = f"{indent}{prefix} {docker_image_with_digest_specifier(image)}{eol}"
            print(f"{path}:[{i + 1}] updating {image.name} sha {sha_str}->{image.sha[:5]}")
            print(f"{ANSI_RED}- {line}{ANSI_RESET}")
            print(f"{ANSI_GREEN}+ {new_line}{ANSI_RESET}")
            lines[i] = new_line
            has_changes = True

    if has_changes:
        path.write_text("\n".join(lines))

    Globals.made_changes |= has_changes


def update_dockerfile(path: Path, skip_images: list[str]):
    update_docker_file("FROM", path, skip_images)


def update_docker_compose_file(path: Path, skip_images: list[str]):
    update_docker_file("image:", path, skip_images)


def main():
    skip_images = ["makeradmin/test", "makeradmin/api", "makeradmin/public", "makeradmin/admin"]
    for compose_file in repo_root_path.rglob("docker-compose*.yml"):
        print(f"Checking {compose_file}")
        update_docker_compose_file(compose_file, skip_images)

    for dockerfile in repo_root_path.rglob("*Dockerfile*"):
        print(f"Checking {dockerfile}")
        update_dockerfile(dockerfile, skip_images)

    return Globals.made_changes


if __name__ == "__main__":
    sys.exit(main())
