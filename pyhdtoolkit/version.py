VERSION = "1.1.1"


def version_info() -> str:
    """Debug convenience function to give version, platform and runtime information."""
    import platform
    import sys

    from pathlib import Path

    info = {
        "PyhDToolkit version": VERSION,
        "Install path": Path(__file__).resolve().parent,
        "Python version": f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}",
        "Python implementation": sys.version,
        "Platform": platform.platform(),
    }
    return "\n".join("{:>24} {}".format(k + ":", str(v).replace("\n", " ")) for k, v in info.items())
