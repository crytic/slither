from shutil import get_terminal_size
from typing import List, Dict, Union

from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Themes

from slither.utils.colors import Colors


class MyPrettyTable:
    def __init__(
        self,
        field_names: List[str],
        pretty_align: bool = True,
        max_width: Union[int, None] = "max",  # Default value is "max"
    ):
        self._field_names = field_names
        self._rows: List = []
        self._options: Dict = {}
        if pretty_align:
            self._options["set_alignment"] = []
            self._options["set_alignment"] += [(field_names[0], "l")]
            for field_name in field_names[1:]:
                self._options["set_alignment"] += [(field_name, "r")]
        else:
            self._options["set_alignment"] = []

        self.max_width = None
        if max_width == "max":
            # We use (0,0) as a fallback to detect if we are not attached to a terminal
            # In this case, we fall back to the default behavior (i.e. printing as much as possible)
            terminal_column = get_terminal_size((0, 0)).columns
            if terminal_column != 0:
                # We reduce slightly the max-width to take into account inconsistencies in terminals
                self.max_width = terminal_column - 3
        else:
            self.max_width = max_width

    def add_row(self, row: List[Union[str, List[str]]]) -> None:
        self._rows.append(row)

    def to_pretty_table(self) -> PrettyTable:
        if Colors.COLORIZATION_ENABLED:
            table = ColorTable(self._field_names, theme=Themes.OCEAN)
        else:
            table = PrettyTable(self._field_names)

        if self.max_width is not None:
            table.max_table_width = self.max_width

        for row in self._rows:
            table.add_row(row)
        if len(self._options["set_alignment"]):
            for column_header, value in self._options["set_alignment"]:
                table.align[column_header] = value
        return table

    def to_json(self) -> Dict:
        return {"fields_names": self._field_names, "rows": self._rows}

    def __str__(self) -> str:
        return str(self.to_pretty_table())


# UTILITY FUNCTIONS


def make_pretty_table(
    headers: list, body: dict, totals: bool = False, total_header="TOTAL"
) -> MyPrettyTable:
    """
    Converts a dict to a MyPrettyTable.  Dict keys are the row headers.
    Args:
        headers: str[] of column names
        body: dict of row headers with a dict of the values
        totals: bool optional add Totals row
        total_header: str optional if totals is set to True this will override the default "TOTAL" header
    Returns:
        MyPrettyTable
    """
    table = MyPrettyTable(headers)
    for row in body:
        table_row = [row] + [body[row][key] for key in headers[1:]]
        table.add_row(table_row)
    if totals:
        table.add_row([total_header] + [sum(body[row][key] for row in body) for key in headers[1:]])
    return table
