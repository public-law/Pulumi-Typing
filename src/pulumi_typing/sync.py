"""Follow a released Pulumi SDK and generate baseline Python stubs."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path

from .transform import transform


def run(package: str, output: Path) -> None:
    module = package.replace("-", "_")
    output = output.resolve()

    with tempfile.TemporaryDirectory(prefix="pulumi-typing-") as tmp:
        root = Path(tmp)
        installed = root / "installed"
        subprocess.run(
            [
                sys.executable, "-m", "pip", "install",
                "--disable-pip-version-check", "--target", str(installed),
                package,
            ],
            check=True,
        )

        distributions = metadata.distributions(path=[str(installed)])
        distribution = next(
            (
                dist for dist in distributions
                if dist.metadata["Name"].lower().replace("_", "-") == package.lower().replace("_", "-")
            ),
            None,
        )
        if distribution is None:
            raise RuntimeError(f"Could not find distribution metadata for {package}")

        module_path = installed / module
        if not module_path.is_dir():
            raise RuntimeError(f"Cannot locate module {module}")

        # Point Pyright at the exact SDK version installed in the temporary directory.
        (root / "pyrightconfig.json").write_text(
            json.dumps({"extraPaths": [str(installed)], "include": []})
        )
        subprocess.run(["pyright", "--createstub", module], cwd=root, check=True)

        stub_path = root / "typings" / module
        if not stub_path.is_dir():
            raise RuntimeError(f"Pyright did not generate stubs for {module}")

        destination = output / f"{module}-stubs" / module
        if destination.parent.exists():
            shutil.rmtree(destination.parent)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stub_path, destination)

        changed = transform(destination, module_path)
        manifest = {
            "package": package,
            "version": distribution.version,
            "transformations": changed,
        }
        (destination.parent / "upstream.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        print(json.dumps(manifest))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", default="pulumi-cloudflare")
    parser.add_argument("--output", type=Path, default=Path("generated"))
    args = parser.parse_args()
    run(args.package, args.output)


if __name__ == "__main__":
    main()
