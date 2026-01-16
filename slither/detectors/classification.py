from typing import Dict, Callable

from slither.utils.colors import green, yellow, red
from slither.utils.comparable_enum import ComparableEnum


class DetectorClassification(ComparableEnum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    INFORMATIONAL = 3
    OPTIMIZATION = 4

    UNIMPLEMENTED = 999


classification_colors: Dict[DetectorClassification, Callable[[str], str]] = {
    DetectorClassification.INFORMATIONAL: green,
    DetectorClassification.OPTIMIZATION: green,
    DetectorClassification.LOW: green,
    DetectorClassification.MEDIUM: yellow,
    DetectorClassification.HIGH: red,
}

classification_txt = {
    DetectorClassification.INFORMATIONAL: "Informational",
    DetectorClassification.OPTIMIZATION: "Optimization",
    DetectorClassification.LOW: "Low",
    DetectorClassification.MEDIUM: "Medium",
    DetectorClassification.HIGH: "High",
}
