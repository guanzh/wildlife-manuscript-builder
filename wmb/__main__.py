"""Allow `python -m wmb`."""

from wmb.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
