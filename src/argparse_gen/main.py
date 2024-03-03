#!/usr/bin/python3

"""
Argparse code generator.
"""

import argparse
import sys

# from call_args import call_args_attr

import argparse_gen.argparse_gen


def main() -> int:
    """
    Argparse code generator.
    """
    parser = argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__,
    )
    parser.add_argument(
        "module_file",
        type=str,
        help=(
            "A .py file of the module containing the callable to be invoked"
            " with CLI arguments."
        ),
    )
    parser.add_argument(
        "obj_name",
        type=str,
        help=(
            "The name of the callable in `module` for which we\"re building"
            ' a CLI interface. This may contain "paths" (like `"foo.bar"`).'
        ),
    )
    parser.add_argument(
        "-p",
        "--param_regex",
        default="^:param\\s+(?P<name>\\w+):\\s*",
        type=str,
        help=(
            "A regular expression to recognise parameters in the callable's"
            " docstring. The default recognizes rST (reStructuredText)"
            " format."
        ),
    )
    parser.add_argument(
        "-i",
        "--indent",
        default="",
        type=str,
        help="Additional indentation for the generated code.",
    )
    parser.add_argument(
        "-s",
        "--skip_private",
        default=True,
        action="store_false",
        help=(
            "Skip private (those with names starting with an underscore)"
            " arguments."
        ),
    )
    parser.add_argument(
        "-c",
        "--call_args",
        default=False,
        dest="use_call_args",
        action="store_true",
        help=(
            "Instead of generating a call with all of the available"
            " arguments, use `call_args` (from the"
            " [`call-args`](https://pypi.org/project/call-args/) package)."
            " This loses some transparency, but it's quite convenient if you"
            " frequently change the arguments."
        ),
    )

    args = parser.parse_args()

    print(
        # call_args_attr(argparse_gen.ArgparseGen.from_file, args).as_code()
        argparse_gen.argparse_gen.ArgparseGen.from_file(
            args.module_file,
            args.obj_name,
            param_regex=args.param_regex,
            indent=args.indent,
            skip_private=args.skip_private,
            use_call_args=args.use_call_args,
        ).as_code(),
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
