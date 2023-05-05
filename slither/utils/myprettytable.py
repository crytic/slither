from typing import List, Dict, Union

from prettytable import PrettyTable


class MyPrettyTable:
    def __init__(self, field_names: List[str], pretty_align: bool = True): #TODO: True by default?
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

    def add_row(self, row: List[Union[str, List[str]]]) -> None:
        self._rows.append(row)


    def to_pretty_table(self) -> PrettyTable:
        table = PrettyTable(self._field_names)
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


# **Dict to MyPrettyTable utility functions**

def make_pretty_table(headers: list, body: dict, totals: bool = False, total_header="TOTAL") -> MyPrettyTable:
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
        table.add_row(["TOTAL"] + [sum([body[row][key] for row in body]) for key in headers[1:]])
    return table

def make_pretty_table_simple(data: dict, first_column_header, second_column_header="") -> MyPrettyTable:
    """
    Converts a dict to a MyPrettyTable.  Dict keys are the row headers.
    Args:
        data: dict of row headers with a dict of the values
        column_header: str of column name for 1st column
    Returns:
        MyPrettyTable
    """

    table = MyPrettyTable([first_column_header, second_column_header])
    for k, v in data.items():
        table.add_row([k] + [v])
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
