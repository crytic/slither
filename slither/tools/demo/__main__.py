import logging
from slither import Slither

import typer

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-demo")


demo_app = SlitherApp(help="Demo tool.")
app.add_typer(demo_app, name="demo")


@demo_app.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    target: target_type,
) -> None:
    state = ctx.ensure_object(SlitherState)

    # Perform slither analysis on the given filename
    _slither = Slither(target.target, **state)

    logger.info("Analysis done!")


if __name__ == "__main__":
    demo_app()
