"""Module for generating Cappa CLI implementations from CommandInfo objects."""

from __future__ import annotations

import dataclasses
import functools
import operator
from typing import TYPE_CHECKING, Annotated, Any, Literal

import cappa

from clinspector.synthesis import is_help_param


if TYPE_CHECKING:
    from clinspector.models.commandinfo import CommandInfo
    from clinspector.models.param import Param


def _class_name(name: str) -> str:
    parts = name.replace("-", " ").replace("_", " ").split()
    return "".join(p.capitalize() for p in parts) or "Command"


def _annotation(param: Param) -> Any:
    if param.count:
        return int
    if param.is_flag:
        return bool
    base: Any = Literal[tuple(param.choices)] if param.choices else str  # ty: ignore[invalid-type-form]
    return list[base] if param.multiple or param.nargs == -1 else base


def _default(param: Param) -> Any:
    if param.required:
        return dataclasses.MISSING
    if param.default is not None:
        return list(param.default) if isinstance(param.default, tuple) else param.default
    if param.count:
        return 0
    if param.is_flag:
        return False
    if param.multiple or param.nargs == -1:
        return dataclasses.field(default_factory=list)
    return None


def _create_field(param: Param) -> tuple[str, Any, Any]:
    """Create a `make_dataclass` field spec for a parameter."""
    shorts = [o for o in param.opts if o.startswith("-") and not o.startswith("--")]
    longs = [o for o in param.opts if o.startswith("--")]
    arg_kwargs: dict[str, Any] = {"help": param.help, "hidden": param.hidden}
    if param.opts:
        arg_kwargs["short"] = shorts or False
        arg_kwargs["long"] = longs or False
    if param.count:
        arg_kwargs["count"] = True
    if param.envvar:
        arg_kwargs["default"] = cappa.Env(param.envvar)
    annotation = _annotation(param)
    default = _default(param)
    if default is None:
        annotation |= None
    hint = Annotated[annotation, cappa.Arg(**arg_kwargs)]
    if isinstance(default, dataclasses.Field):
        return param.name, hint, default
    return param.name, hint, dataclasses.field(default=default)


def _has_default(field: dataclasses.Field[Any]) -> bool:
    return (
        field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING
    )


def create_class(cmd_info: CommandInfo) -> type[Any]:
    """Create a Cappa command class (a dataclass) from a CommandInfo object.

    Subcommands become nested command classes, collected in a `subcommand` field.

    Args:
        cmd_info: The CommandInfo object to convert

    Returns:
        A dataclass decorated with cappa.command
    """
    fields = [_create_field(p) for p in cmd_info.params if not is_help_param(p)]
    # dataclasses require fields without defaults to come first
    fields.sort(key=lambda f: _has_default(f[2]))
    if cmd_info.subcommands:
        sub_classes = [create_class(sub) for sub in cmd_info.subcommands.values()]
        union = functools.reduce(operator.or_, sub_classes)
        hint = Annotated[union, cappa.Subcommand()]  # ty: ignore[invalid-type-form]
        fields.insert(0, ("subcommand", hint, dataclasses.field()))

    def invoke(**kwargs: Any) -> None:
        """Placeholder callback."""
        print(f"Called {cmd_info.name} with: {kwargs}")

    cls = dataclasses.make_dataclass(_class_name(cmd_info.name), fields)
    cls.__doc__ = cmd_info.description or None
    return cappa.command(  # ty: ignore[not-callable]
        cls,
        name=cmd_info.name,
        help=cmd_info.description or None,
        hidden=cmd_info.hidden,
        deprecated=cmd_info.deprecated,
        invoke=invoke,
    )
