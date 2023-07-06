from typing import List, Dict, Union

from prettytable.colortable import ColorTable, Themes


class MyPrettyTable:
    def __init__(self, field_names: List[str]):
        self._field_names = field_names
        self._rows: List = []

    def add_row(self, row: List[Union[str, List[str]]]) -> None:
        self._rows.append(row)

    def to_pretty_table(self) -> ColorTable:
        table = ColorTable(self._field_names, theme=Themes.OCEAN)
        for row in self._rows:
            table.add_row(row)
        return table

    def to_json(self) -> Dict:
        return {"fields_names": self._field_names, "rows": self._rows}

    def __str__(self) -> str:
        return str(self.to_pretty_table())


# **Dict to MyPrettyTable utility functions**

def make_pretty_table(headers: list, body: dict, totals: bool = False) -> MyPrettyTable:
    """
    Converts a dict to a MyPrettyTable.  Dict keys are the row headers.
    Args:
        data: dict of row headers with a dict of the values
        column_header: str of column name for 1st column
    Returns:
        MyPrettyTable
    """
    table = MyPrettyTable(headers)
    for row in body:
        table_row = [row] + [body[row][key] for key in headers[1:]]
        table.add_row(table_row)
    if totals:
        table.add_row(["Total"] + [sum([body[row][key] for row in body]) for key in headers[1:]])
    return table


def transpose(table):
    """
    Converts a dict of dicts to a dict of dicts with the keys transposed
    Args:
        table: dict of dicts
    Returns:
        dict of dicts

    Example:
        in:
        {
            "dep": {"loc": 0, "sloc": 0, "cloc": 0},
            "test": {"loc": 0, "sloc": 0, "cloc": 0},
            "src": {"loc": 0, "sloc": 0, "cloc": 0},
        }
        out:
        {
            'loc': {'dep': 0, 'test': 0, 'src': 0},
            'sloc': {'dep': 0, 'test': 0, 'src': 0},
            'cloc': {'dep': 0, 'test': 0, 'src': 0},
        }
    """
    any_key = list(table.keys())[0]
    return {
        inner_key: {outer_key: table[outer_key][inner_key] for outer_key in table}
        for inner_key in table[any_key]
    }
