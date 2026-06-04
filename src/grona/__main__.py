"""Run Grona with `python -m grona`."""

from __future__ import annotations

import sys

if "--benchmark-demo" in sys.argv[1:]:
    from .benchmark_cli import main as benchmark_main

    raise SystemExit(benchmark_main(sys.argv[1:]))

from .cli import main

raise SystemExit(main())
