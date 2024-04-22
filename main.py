"""With the update in the project's file structure, this file is used to run it in this dir as a dev."""

from __future__ import annotations

import hypickle.main
import sys

def main() -> None:
    hypickle.main.main(sys.argv)

if __name__ == '__main__':
    main()