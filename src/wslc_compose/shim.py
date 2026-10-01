"""`wslc` wrapper command: adds a `compose` subcommand like docker/podman.

`wslc compose up -d`   -> wslc-compose up -d
`wslc <anything else>` -> passed through verbatim to the real wslc CLI
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Optional, Tuple

from wslc_compose import cli, engine


def split_argv(argv: List[str]) -> Tuple[Optional[List[str]], List[str]]:
    """Return (compose_args, passthrough_args); exactly one is meaningful."""
    if argv and argv[0] == "compose":
        return argv[1:], []
    return None, argv


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    # Circuit breaker: mark this process so engine.find_wslc() never consults
    # shutil.which(). If a shim for this very wrapper is on PATH (pipx/uv/
    # scoop shims), which() would find it and re-invoke it without bound —
    # the _is_self() guard compares against sys.argv[0], which does not match
    # the shim launcher's path. The marker is inherited by child processes,
    # so every nesting level is guarded. Children also receive it via the
    # environment, keeping engine calls in this process on the fallback path.
    os.environ[engine.SHIM_GUARD_ENV] = "1"
    compose_args, passthrough = split_argv(argv)
    if compose_args is not None:
        return cli.main(compose_args or ["--help"])
    try:
        wslc = engine.find_wslc()
    except engine.WslcError as exc:
        print(f"wslc: {exc}", file=sys.stderr)
        return 1
    try:
        return subprocess.call([wslc] + passthrough)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
