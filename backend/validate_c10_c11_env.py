from __future__ import annotations

import importlib
import sys


REQUIRED_MODULES = ("pandas", "openpyxl")


def main() -> int:
    missing: list[str] = []

    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)

    if missing:
        print(
            "Faltan dependencias de parseo para C-10/C-11: "
            + ", ".join(sorted(missing))
        )
        print("Instalalas con: python -m pip install -e .[test]")
        return 1

    print("OK: pandas y openpyxl están disponibles en el entorno activo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
