#!/usr/bin/env python3
import enum
import logging
from typing import Annotated, Optional

import typer

from slither.__main__ import app
from slither.utils.command_line import SlitherState, SlitherApp, GroupWithCrytic

similarity: SlitherApp = SlitherApp()
app.add_typer(similarity, name="simil")


logging.basicConfig()
logger = logging.getLogger("Slither-simil")

modes = ["info", "test", "train", "plot"]


class Mode(str, enum.Enum):
    info = "info"
    test = "test"
    train = "train"
    plot = "plot"


@similarity.callback(cls=GroupWithCrytic)
def main_callback(
    ctx: typer.Context,
    mode: Annotated[Mode, typer.Option(help="Operation mode")] = Mode.info,
    model: Annotated[str, typer.Argument(help="Model filename")] = "model.bin",
    filename: Annotated[
        Optional[str], typer.Option("--filename", help="Contract file name (e.g., contract.sol)")
    ] = None,
    fname: Annotated[Optional[str], typer.Option("--fname", help="Target function name")] = None,
    ext: Annotated[
        Optional[str], typer.Option("--ext", help="Extension to filter contracts by")
    ] = None,
    nsamples: Annotated[
        int, typer.Option("--nsamples", help="Number of contract samples used for training")
    ] = 0,
    ntop: Annotated[
        int, typer.Option(help="Number of most similar contracts to show for testing")
    ] = 10,
    input_: Annotated[
        Optional[str], typer.Option("--input", help="File or directory used as input")
    ] = None,
) -> None:
    """Code similarity detection tool.

    For usage, see https://github.com/crytic/slither/wiki/Code-Similarity-detector
    """

    default_log = logging.INFO
    logger.setLevel(default_log)

    state = ctx.ensure_object(SlitherState)
    state.update(
        {
            "model": model,
            "filename": filename,
            "fname": fname,
            "ext": ext,
            "nsamples": nsamples,
            "ntop": ntop,
            "input_": input_,
        }
    )

    from slither.tools.similarity.info import info
    from slither.tools.similarity.test import test
    from slither.tools.similarity.train import train
    from slither.tools.similarity.plot import plot

    mapping = {
        Mode.info: info,
        Mode.test: test,
        Mode.train: train,
        Mode.plot: plot,
    }

    func = mapping[mode]
    func(**state)


def main():
    """Entry point for the slither-simil CLI."""
    similarity()


if __name__ == "__main__":
    main()

# endregion
