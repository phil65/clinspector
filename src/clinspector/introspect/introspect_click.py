from __future__ import annotations

import click

from clinspector.models import commandinfo, param


def parse(
    command: click.Command,
    parent: click.Context | None = None,
) -> commandinfo.CommandInfo:
    """Get a `CommandInfo` dataclass for given click `Command`.

    Args:
        command: The **click** `Command` to get info for.
        parent: The optional parent context
    """
    import click

    ctx = click.Context(command, parent=parent)
    subcommands = getattr(command, "commands", {})
    dct = ctx.command.to_info_dict(ctx)
    formatter = ctx.make_formatter()
    pieces = ctx.command.collect_usage_pieces(ctx)
    formatter.write_usage(ctx.command_path, " ".join(pieces), prefix="")
    usage = formatter.getvalue().rstrip("\n")
    # Generate the full usage string based on parents if any, i.e. `root sub1 sub2 ...`.
    full_path = []
    current: click.Context | None = ctx
    while current is not None:
        name = current.command.name.lower() if current.command.name else ""
        full_path.append(name)
        current = current.parent
    full_path.reverse()
    return commandinfo.CommandInfo(
        name=ctx.command.name or "",
        description=ctx.command.help or ctx.command.short_help or "",
        usage=" ".join(full_path) + usage,
        params=[param.Param(**i) for i in dct["params"]],
        subcommands={k: parse(v, parent=ctx) for k, v in subcommands.items()},
        deprecated=dct["deprecated"],
        epilog=dct["epilog"],
        hidden=dct["hidden"],
    )


def get_info(
    instance: click.Group,
    command: str | None = None,
) -> commandinfo.CommandInfo:
    """Return a `CommmandInfo` object for command of given click Group.

    Args:
        instance: A `Typer`, **click** `Group` or `ArgumentParser` instance
        command: The command to get info for.
    """
    info = parse(instance)
    if command:
        ctx = click.Context(instance)
        subcommands = getattr(instance, "commands", {})
        cmds = {k: parse(v, parent=ctx) for k, v in subcommands.items()}
        return cmds.get(command, info)
    return info


if __name__ == "__main__":
    import mkdocs.__main__

    info = get_info(mkdocs.__main__.cli, command="mkdocs")
    print(info)
