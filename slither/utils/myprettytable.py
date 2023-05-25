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
