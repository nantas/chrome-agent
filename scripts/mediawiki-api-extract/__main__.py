"""CLI entry point for MediaWiki API extraction pipeline."""

import os
import sys

# When invoked as `python3 scripts/mediawiki-api-extract` (directory as script),
# Python cannot resolve relative imports because the hyphenated directory name
# is not a valid package identifier.  Re-invoke ourselves via -m which handles
# the hyphenated package name correctly.
if __name__ == "__main__" and __package__ in (None, "", "__main__"):
    import subprocess
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "scripts.mediawiki-api-extract"] + sys.argv[1:]
        )
    )

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
