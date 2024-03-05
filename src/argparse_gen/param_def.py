import enum
import inspect
import operator
from typing import Any, get_args, _LiteralGenericAlias

from .utils import EnumValue, EnumType, str_as_arg


class ParamDef:
    """
    One parameter definition.
    """

    _repr_f = {
        "type": operator.attrgetter("__name__"),
    }

    def __init__(
        self,
        param: inspect.Parameter,
        help_str: str | None,
    ) -> None:
        self.param = param
        self.names: list[str] = list()
        self.help_str = help_str

    def set_names(self, single_chars: set[str]) -> None:
        """
        Update `self.names`.
        """
        name = self.param.name
        if self.param.kind is inspect.Parameter.POSITIONAL_ONLY:
            self.names = [name]
        else:
            if len(name) == 1:
                single_chars.add(name)
                self.names = [f"-{name}"]
            else:
                first_char = name[0]
                if first_char not in single_chars:
                    single_chars.add(first_char)
                    self.names = [f"-{first_char}", f"--{name}"]
                else:
                    self.names = [f"--{name}"]

    def _handle_annotation(self, result: dict[str, Any]) -> None:
        """
        Analize param's annotation and update its dictionary representation.
        """
        param_type: type | None = None
        choices: tuple[Any, ...] | None = None
        annotation = self.param.annotation
        if type(annotation) is _LiteralGenericAlias:
            choices = get_args(annotation)
            param_types = {type(literal) for literal in choices}
            if len(param_types) == 1:
                param_type = param_types.pop()
        elif inspect.isclass(annotation) and issubclass(annotation, enum.Enum):
            choices = [EnumValue(enum_value) for enum_value in annotation]
            param_type = EnumType(annotation)
            try:
                result["default"] = EnumValue(result["default"])
            except KeyError:
                pass
        elif isinstance(annotation, type):
            param_type = annotation
        if param_type is not None:
            if param_type is bool:
                result["action"] = (
                    "store_false"
                    if self.param.default is True else
                    "store_true"
                )
            else:
                result["type"] = param_type
        if choices is not None:
            result["choices"] = choices

    def as_dict(self) -> dict[str, Any]:
        """
        Return attributes for :py:meth:`ArgumentParser.add_argument` as a dict.
        """
        result = {"names": self.names}
        required = self.param.default is inspect.Parameter.empty
        if self.param.kind == inspect.Parameter.POSITIONAL_ONLY:
            if not required:
                result["nargs"] = "?"
        else:
            result["required"]: required
        if not required:
            result["default"] = self.param.default
        self._handle_annotation(result)
        result["help"] = self.help_str or ""
        return result

    def as_repr_dict(self) -> dict[str, str]:
        """
        Return attributes as a dict of `repr` strings.
        """
        return {
            name: self._repr_f.get(name, repr)(value)
            for name, value in self.as_dict().items()
        }

    def as_code(self) -> str:
        """
        Return attributes as :py:meth:`ArgumentParser.add_argument` code.
        """
        lines = (
            [repr(name) for name in self.names]
            + [
                str_as_arg(name, value)
                for name, value in self.as_repr_dict().items()
                if name != "names"
            ]
        )
        return (
            "parser.add_argument(\n"
            + "".join(f"    {line},\n" for line in lines)  # noqa: E231
            + ")"
        )

    def as_arg(self) -> str:
        """
        Return attributes as code for the main CLI wrapper call.
        """
        return (
            f"args.{self.param.name}"
            if self.param.kind is inspect.Parameter.POSITIONAL_ONLY else
            f"{self.param.name}=args.{self.param.name}"
        )
