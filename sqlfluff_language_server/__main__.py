import sys
import argparse
import logging

from .server import sqlfluff_server


def get_version() -> str:
    """Get the program version."""
    try:
        from importlib.metadata import version  # type: ignore
    except ImportError:
        try:
            from importlib_metadata import version  # type: ignore
        except ImportError:
            print(
                "Error: unable to get version. "
                "If using Python < 3.8, you must install "
                "`importlib_metadata` to get the version.",
                file=sys.stderr,
            )
            sys.exit(1)
    return version("sqlfluff_language_server")


def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "sqlfluff-language-server"

    parser.add_argument(
        "--version",
        help="display version information and exit",
        action="store_true",
    )
    parser.add_argument(
        "--tcp", action="store_true", help="Use TCP server instead of stdio"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind to this address")
    parser.add_argument("--port", type=int, default=2087, help="Bind to this port")
    parser.add_argument(
        "--log-file",
        help="redirect logs to the given file instead of writing to stderr",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase verbosity of log output",
        action="count",
        default=0,
    )


def main():
    logging.getLogger("sqlfluff").setLevel(logging.WARN)

    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    if args.version:
        print(get_version())
        sys.exit(0)

    log_level = {0: logging.INFO, 1: logging.DEBUG}.get(
        args.verbose,
        logging.DEBUG,
    )

    if args.log_file:
        logging.basicConfig(
            filename=args.log_file,
            filemode="w",
            level=log_level,
        )
    else:
        logging.basicConfig(stream=sys.stderr, level=log_level)
        logging.getLogger("pygls.protocol").setLevel(log_level)

    if args.tcp:
        sqlfluff_server.start_tcp(args.host, args.port)
    else:
        sqlfluff_server.start_io()


if __name__ == "__main__":
    main()
