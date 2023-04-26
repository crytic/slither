from typing import List, Dict, Union

from prettytable import PrettyTable


class MyPrettyTable:
    def __init__(self, field_names: List[str]):
        self._field_names = field_names
        self._rows: List = []

    def add_row(self, row: List[Union[str, List[str]]]) -> None:
        self._rows.append(row)

    def to_pretty_table(self) -> PrettyTable:
        table = PrettyTable(self._field_names)
        for row in self._rows:
            table.add_row(row)
        return table

    def to_json(self) -> Dict:
        return {"fields_names": self._field_names, "rows": self._rows}

    def __str__(self) -> str:
        return str(self.to_pretty_table())


# **Dict to MyPrettyTable utility functions**


# Converts a dict to a MyPrettyTable.  Dict keys are the row headers.
# @param headers str[] of column names
# @param body dict of row headers with a dict of the values
# @param totals bool optional add Totals row
def make_pretty_table(headers: list, body: dict, totals: bool = False) -> MyPrettyTable:
    table = MyPrettyTable(headers)
    for row in body:
        table_row = [row] + [body[row][key] for key in headers[1:]]
        table.add_row(table_row)
    if totals:
        table.add_row(["Total"] + [sum([body[row][key] for row in body]) for key in headers[1:]])
    return table


# takes a dict of dicts and returns a dict of dicts with the keys transposed
# example:
# in:
# {
#     "dep": {"loc": 0, "sloc": 0, "cloc": 0},
#     "test": {"loc": 0, "sloc": 0, "cloc": 0},
#     "src": {"loc": 0, "sloc": 0, "cloc": 0},
# }
# out:
# {
#     'loc': {'dep': 0, 'test': 0, 'src': 0},
#     'sloc': {'dep': 0, 'test': 0, 'src': 0},
#     'cloc': {'dep': 0, 'test': 0, 'src': 0},
# }
def transpose(table):
    any_key = list(table.keys())[0]
    return {
        inner_key: {outer_key: table[outer_key][inner_key] for outer_key in table}
        for inner_key in table[any_key]
    }
