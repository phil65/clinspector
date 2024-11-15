"""Introspection module for cappa CLI applications."""

from __future__ import annotations

import dataclasses
from typing import Any, get_type_hints

import cappa

from clinspector.models import commandinfo, param


def _get_param_from_arg(name: str, arg: cappa.Arg[Any]) -> param.Param:
    """Convert a cappa.Arg to a Param object.

    Args:
        name: Parameter name
        arg: Cappa argument object
    """
    opts = []
    if arg.short:
        opts.append(f"-{arg.short}")
    if arg.long:
        opts.append(f"--{arg.long}")

    return param.Param(
        name=name,
        help=arg.help,
        default=arg.default,
        required=arg.required or False,
        opts=opts,
        # multiple=arg.multiple,
        # is_flag=isinstance(arg.type, bool),
        # metavar=arg.metavar,
        # envvar=arg.env,
        hidden=arg.hidden,
        param_type_name="option" if opts else "argument",
    )


def get_info(cls: type[Any]) -> commandinfo.CommandInfo:
    """Extract CLI information from a cappa dataclass.

    Args:
        cls: Dataclass to analyze

    Raises:
        TypeError: If cls is not a dataclass
    """
    if not dataclasses.is_dataclass(cls):
        msg = f"Expected a dataclass, got {type(cls)}"
        raise TypeError(msg)

    params: list[param.Param] = []
    hints = get_type_hints(cls, include_extras=True)
    params = [
        _get_param_from_arg(field.name, meta)
        for field in dataclasses.fields(cls)
        if (hint := hints.get(field.name)) and hasattr(hint, "__metadata__")
        for meta in hint.__metadata__
        if isinstance(meta, cappa.Arg)
    ]

    return commandinfo.CommandInfo(
        name=cls.__name__.lower(),
        description=cls.__doc__ or "",
        params=params,
        usage=cls.__name__.lower(),
    )


if __name__ == "__main__":
    import typing

    @cappa.command(invoke=print)
    class Test:
        """Test command that demonstrates cappa usage."""

        name: typing.Annotated[str, cappa.Arg(help="Name to greet")]
        count: typing.Annotated[int, cappa.Arg("-c", help="Times to greet")] = 1
        excited: typing.Annotated[bool, cappa.Arg("--excited", "-e")] = False

    info = get_info(Test)
    print(info)
