from typing import List, Dict

from prettytable import PrettyTable


class MyPrettyTable:
    def __init__(self, field_names: List[str]):
        self._field_names = field_names
        self._rows: List = []

    def add_row(self, row):
        self._rows.append(row)

    def to_pretty_table(self) -> PrettyTable:
        table = PrettyTable(self._field_names)
        for row in self._rows:
            table.add_row(row)
        return table

    def to_json(self) -> Dict:
        return {"fields_names": self._field_names, "rows": self._rows}

    def __str__(self):
        return str(self.to_pretty_table())
