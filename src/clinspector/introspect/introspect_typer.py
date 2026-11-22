from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import typer
from typer.core import TyperArgument, TyperOption
from typer.main import get_command

from clinspector.models import commandinfo, param


if TYPE_CHECKING:
    from typer import _click


def _parse_param(p: _click.Parameter) -> param.Param:
    annotation = choices = None
    click_type = getattr(p, "type", None)
    if isinstance(p, TyperOption | TyperArgument) and (
        descriptor := getattr(p, "type_descriptor", None)
    ):
        # typer versions with a type descriptor (original Python annotation)
        annotation = descriptor.annotation
        choices = descriptor.choices
    else:
        # other typer versions only expose the click ParamType
        choices = getattr(click_type, "choices", None)
    opt = p if isinstance(p, TyperOption) else None
    return param.Param(
        name=p.name,
        param_type_name=cast(Literal["option", "parameter", "argument"], p.param_type_name),
        opts=p.opts,
        secondary_opts=p.secondary_opts,
        type=(
            {"name": getattr(annotation, "__name__", str(annotation))}
            if annotation
            else ({"name": click_type.name} if click_type else None)
        ),
        required=p.required,
        nargs=p.nargs,
        multiple=p.multiple,
        default=p.default,
        envvar=p.envvar if isinstance(p.envvar, str) else None,
        help=getattr(p, "help", None),
        hidden=getattr(p, "hidden", False),
        is_eager=p.is_eager,
        metavar=p.metavar,
        choices=[str(c) for c in choices] if choices is not None else None,
        prompt=opt.prompt if opt else None,
        is_flag=opt.is_flag if opt else False,
        flag_value=opt.is_flag if opt else False,
        count=opt.count if opt else False,
    )


def parse(
    command: _click.Command,
    parent: _click.Context | None = None,
) -> commandinfo.CommandInfo:
    """Get a `CommandInfo` dataclass for given Typer (vendored click) `Command`.

    Args:
        command: The `Command` to get info for.
        parent: The optional parent context
    """
    ctx = command.context_class(command, parent=parent)
    subcommands = getattr(command, "commands", {})
    formatter = ctx.make_formatter()
    pieces = command.collect_usage_pieces(ctx)
    formatter.write_usage(ctx.command_path, " ".join(pieces), prefix="")
    usage = formatter.getvalue().rstrip("\n")
    # Generate the full usage string based on parents if any, i.e. `root sub1 sub2 ...`.
    full_path = []
    current: _click.Context | None = ctx
    while current is not None:
        name = current.command.name.lower() if current.command.name else ""
        full_path.append(name)
        current = current.parent
    full_path.reverse()
    return commandinfo.CommandInfo(
        name=command.name or "",
        description=command.help or command.short_help or "",
        usage=" ".join(full_path) + usage,
        params=[_parse_param(p) for p in command.get_params(ctx)],
        subcommands={k: parse(v, parent=ctx) for k, v in subcommands.items()},
        deprecated=bool(command.deprecated),
        epilog=command.epilog,
        hidden=command.hidden,
        callback=command.callback,
    )


def get_info(instance: typer.Typer, command: str | None = None) -> commandinfo.CommandInfo:
    """Return a `CommmandInfo` object for command of given Typer object.

    Args:
        instance: A `Typer`, **click** `Group` or `ArgumentParser` instance
        command: The command to get info for.
    """
    cmd = get_command(instance)
    info = parse(cmd)
    if command:
        ctx = typer.Context(cmd)
        subcommands = getattr(cmd, "commands", {})
        cmds = {k: parse(v, parent=ctx) for k, v in subcommands.items()}
        return cmds.get(command, info)
    return info


if __name__ == "__main__":
    from mkdocs_mknodes import cli

    info = get_info(cli.cli, command="mkdocs")
    print(info)
