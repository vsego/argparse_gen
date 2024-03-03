# `Argparse` Code Generator

A simple utility meant to generate the skeleton for the
[`argparse`](https://docs.python.org/3/library/argparse.html) interface of your
CLI scripts.

## Content

1. [Intro](#intro)
2. [Installation](#installation)
3. [Usage](#usage)
4. [CLI arguments](#cli-arguments)

## Intro

This package provides a simple utility to generate basic
[`argparse`](https://docs.python.org/3/library/argparse.html) interface for CLI
scripts. It works by analysing the callable that you wish your script to call
based on CLI arguments.

More precisely, it gets:

1. the list of arguments from callable's signature;

2. help hints from the callable's docstring;

3. types, if possible, from callable's type annotation.

In some cases, it can do a bit more. For example, if the type of an argument is
`bool`, the script will add `action` to its `add_argument` call, and if it is a
`Literal` or an `enum.Enum`, it will create `choices`.

## Installation

Just install it from PyPI:

```bash
$ pip install argparse_gen
```

This'll make `argparse_gen` script and package available to you.

## Usage

If you run

```bash
$ argparse_gen -h
```

you'll get the full help for it, but essentially, it's used by calling

```bash
$ argparse_gen path/to/your/package/ name_of_callable_in_that_package
```

or

```bash
$ argparse_gen path/to/your/module.py name_of_callable_in_that_module
```

The output of the script is Python code that you can copy paste to your
script's main file, and then adjust to your needs (the autogenerated version
is unlikely to be perfect, except maybe for really trivial stuff).

If you wish to create your own custom scripts to prepare this code, use the
package `argparse_gen` which exposes `ArgparseGen` class (which implements the
whole thing), `ParamDef` (which implements one parameter), and `main` function
(which wraps the class for convenient calls).

## CLI arguments

The script recognizes the following CLI arguments:

* `-p PARAM_REGEX`, `--param_regex PARAM_REGEX`: A regular expression to recognise parameters in the callable's docstring. The default recognizes rST (reStructuredText) format.
* `-i INDENT`, `--indent INDENT`: Additional indentation for the generated code.
* `-s, --skip_private`: Skip private (those with names starting with an underscore) arguments.
* `-c, --call_args`: Instead of generating a call with all of the available arguments, use `call_args` (from the [`call-args`](https://pypi.org/project/call-args/) package). This loses some transparency, but it's quite convenient if you frequently change the arguments.
