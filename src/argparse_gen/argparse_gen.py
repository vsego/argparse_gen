"""
Argparse code generator.
"""

import importlib
import inspect
import operator
from pathlib import Path
import re
import sys
import textwrap
from types import ModuleType
from typing import Self, Any

from .param_def import ParamDef


class ArgparseGen:
    """
    Argparse code generator.
    """

    module_name_base = "argparse_gen_load"

    def __init__(
        self,
        module: ModuleType,
        obj_name: str,
        *,
        param_regex: str = r"^:param\s+(?P<name>\w+):\s*",
        indent: str = "",
        skip_private: bool = True,
        use_call_args: bool = False,
    ) -> None:
        """
        Initialise `ArgparseGen` instance.

        :param module: A module containing the callable to be invoked with CLI
            arguments.
        :param obj_name: The name of the callable in `module` for which we're
            building a CLI interface. This may contain "paths" (like
            `"foo.bar"`).
        :param param_regex: A regular expression to recognise parameters in the
            callable's docstring. The default recognizes rST (reStructuredText)
            format.
        :param indent: Additional indentation for the generated code.
        :param skip_private: Skip private (those with names starting with an
            underscore) arguments.
        :param use_call_args: Instead of generating a call with all of the
            available arguments, use `call_args` (from the
            [`call-args`](https://pypi.org/project/call-args/) package). This
            loses some transparency, but it's quite convenient if you
            frequently change the arguments.
        """
        self.module = module
        self.obj_name = obj_name
        self.param_re = re.compile(param_regex)
        self.indent = indent
        self.skip_private = skip_private
        self.use_call_args = use_call_args

    @classmethod
    def _get_name(cls, name: str | None = None) -> str:
        """
        Return a name to be used for a loaded module.
        """
        n = 0
        while name is None or name in sys.modules:
            suffix = f"_{n}" if n else ""
            name = f"{cls.module_name_base}{suffix}"
            n += 1
        return name

    @classmethod
    def from_file(
        cls,
        module_path: Path | str,
        obj_name: str,
        *,
        param_regex: str = r"^:param\s+(?P<name>\w+):\s*",
        indent: str = "",
        skip_private: bool = True,
        use_call_args: bool = False,
    ) -> Self:
        """
        Return an `ArgparseGen` instance from a module file or a package dir.
        """
        module: ModuleType
        path = (
            module_path
            if isinstance(module_path, Path) else
            Path(module_path)
        )
        if path.is_dir:
            sys.path.insert(0, path.parent)
            module = importlib.import_module(path.stem)
        else:
            module_name = cls._get_name(path.stem)
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return cls(
            module,
            obj_name=obj_name,
            param_regex=param_regex,
            indent=indent,
            skip_private=skip_private,
            use_call_args=use_call_args,
        )

    @classmethod
    def from_string(
        cls,
        source: str,
        obj_name: str,
        *,
        param_regex: str = r"^:param\s+(?P<name>\w+):\s*",
        indent: str = "",
        skip_private: bool = True,
        use_call_args: bool = False,
    ) -> Self:
        """
        Return an `ArgparseGen` instance from a module as a source string.
        """
        spec = importlib.util.spec_from_loader(cls._get_name(), loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(source, module.__dict__)
        spec.loader.exec_module(module)
        return cls(
            module,
            obj_name=obj_name,
            param_regex=param_regex,
            indent=indent,
            skip_private=skip_private,
            use_call_args=use_call_args,
        )

    def _get_obj(self) -> Any:
        """
        Return object to call from CLI.
        """
        return operator.attrgetter(self.obj_name)(self.module)

    def _get_help_dict(self, obj: Any) -> dict[str, str]:
        """
        Return a dictionary of help items from docstring in `obj`.
        """
        def save_current() -> None:
            nonlocal result, curr_name, curr_help
            if curr_name and curr_help:
                result[curr_name] = curr_help

        result: dict[str, str] = dict()
        if not obj.__doc__:
            return result

        curr_name = ""
        curr_help = ""
        for line in obj.__doc__.split("\n"):
            line = line.strip()
            if not line:
                save_current()
            elif m := self.param_re.search(line):
                save_current()
                curr_name = m.group("name")
                curr_help = line[m.end() - m.start():]
            elif curr_name:
                curr_help += ("" if curr_help.endswith(" ") else " ") + line
        save_current()

        if inspect.isclass(obj):
            try:
                obj = obj.__init__
            except AttributeError:
                pass
            else:
                result.update(self._get_help_dict(obj))

        return result

    def as_list(self) -> list[ParamDef]:
        """
        Return arguments for `ArgumentParser` as list of `ParamDef` instances.
        """
        obj = self._get_obj()
        helps = self._get_help_dict(obj)
        single_chars: set[str] = set()
        result = [
            ParamDef(param, helps.get(param.name))
            for param in inspect.signature(obj).parameters.values()
            if (
                not (self.skip_private and param.name.startswith("_"))
                and param.kind in {
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                }
            )
        ]
        for param_def in sorted(
            result, key=lambda param_def: len(param_def.param.name),
        ):
            param_def.set_names(single_chars)
        return result

    def as_args(self) -> str:
        """
        Return arguments for `obj(...)` call as a string.
        """
        return "".join(
            f"        {param_def.as_arg()},\n"  # noqa: E231
            for param_def in self.as_list()
        )

    def as_code(self) -> str:
        """
        Return full code for CLI script to use `obj`.
        """
        lines = [
            "#!/usr/bin/python3",
            "",
        ]
        try:
            doc = self._get_obj().__doc__.strip().splitlines()[0].strip()
        except (AttributeError, IndexError):
            pass
        else:
            lines.extend([
                "'''",
                doc,
                "'''",
                "",
            ])
        lines.extend([
            "import argparse",
            "import sys",
        ])
        if self.use_call_args:
            lines.extend([
                "",
                "from call_args import call_args_attr",
            ])
        module_name = self.module.__name__
        use_module = module_name and not module_name.startswith("__")
        if use_module:
            lines.extend([
                "",
                f"import {self.module.__name__}",
            ])
        lines.extend(
            [
                "",
                "",
                "if __name__ == '__main__':",
                "    parser = argparse.ArgumentParser(",
                "        description=sys.modules[__name__].__doc__,",
                "    )",
            ]
            + [
                textwrap.indent(param_def.as_code(), "    ")
                for param_def in self.as_list()
            ]
            + [
                "",
                "    args = parser.parse_args()",
                "",
            ],
        )
        prefix = f"{self.module.__name__}." if use_module else ""
        obj_name = self.obj_name
        lines.append(
            f"    call_args_attr({prefix}{obj_name}, args)"
            if self.use_call_args else
            f"    {prefix}{obj_name}(\n{self.as_args()}    )"  # noqa: E202
        )
        return textwrap.indent("\n".join(lines), self.indent)
