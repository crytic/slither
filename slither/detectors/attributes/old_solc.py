"""
    Check if an old version of solc is used
    Solidity >= 0.4.23 should be used
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re

class OldSolc(AbstractDetector):
    """
    Check if an old version of solc is used
    """

    ARGUMENT = 'solc-version'
    HELP = 'Old versions of Solidity (< 0.4.23)'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#old-versions-of-solidity'

    CAPTURING_VERSION_PATTERN = re.compile("(?:(\d+|\*|x|X)\.(\d+|\*|x|X)\.(\d+|\*|x|X)|(\d+|\*|x|X)\.(\d+|\*|x|X)|(\d+|\*|x|X))")
    VERSION_PATTERN = "(?:(?:\d+|\*|x|X)\.(?:\d+|\*|x|X)\.(?:\d+|\*|x|X)|(?:\d+|\*|x|X)\.(?:\d+|\*|x|X)|(?:\d+|\*|x|X))"
    SPEC_PATTERN = re.compile(f"(?:(?:(\^|\~|\>\s*=|\<\s*\=|\<|\>|\=|v)\s*({VERSION_PATTERN}))|(?:\s*({VERSION_PATTERN})\s*(\-)\s*({VERSION_PATTERN})\s*))(?:\s*\|\|\s*|\s*)")


    # Indicates the highest disallowed version.
    DISALLOWED_THRESHOLD = "0.4.22"

    class SemVerVersion(object):

        MAX_DIGIT_VALUE = 2**256
        MIN_DIGIT_VALUE = -(2**256)

        def __init__(self, version, original_length=3):
            if not isinstance(version, list) or len(version) != 3:
                raise NotImplementedError("SemVer versions can only be initialized with a 3-element list.")
            self.version = version
            self.original_length = original_length

        def __str__(self):
            return f"{self.version[0] if self.version[0] is not None else '*'}.{self.version[1] if self.version[1] is not None else '*'}.{self.version[2] if self.version[2] is not None else '*'}"

        def __eq__(self, other):
            if not isinstance(other, OldSolc.SemVerVersion):
                return False

            # Loop through all digits looking for differences.
            for i in range(0, len(self.version)):
                if self.version[i] is None or other.version[i] is None or self.version[i] == other.version[i]:
                    continue
                else:
                    return False

            # We could not find a difference, they are equal.
            return True

        def __ne__(self, other):
            if not isinstance(other, OldSolc.SemVerVersion):
                return True
            return self.version != other.version

        def __lt__(self, other):
            if not isinstance(other, OldSolc.SemVerVersion):
                return False

            # Loop through all digits looking for one which is less.
            for i in range(0, len(self.version)):
                self_digit = self.MIN_DIGIT_VALUE if self.version[i] is None else self.version[i]
                other_digit = self.MIN_DIGIT_VALUE if other.version[i] is None else other.version[i]
                if self_digit == other_digit:
                    continue
                elif self_digit < other_digit:
                    return True
                else:
                    return False

            # If we reach here, they are equal.
            return False

        def __le__(self, other):
            if not isinstance(other, OldSolc.SemVerVersion):
                return False
            return self == other or self < other

        def __gt__(self, other):
            if not isinstance(other, OldSolc.SemVerVersion):
                return False

            # Loop through all digits looking for one which is greater.
            for i in range(0, len(self.version)):
                self_digit = self.MAX_DIGIT_VALUE if self.version[i] is None else self.version[i]
                other_digit = self.MAX_DIGIT_VALUE if other.version[i] is None else other.version[i]
                if self_digit == other_digit:
                    continue
                elif self_digit > other_digit:
                    return True
                else:
                    return False

            # If we reach here, they are equal.
            return False

        def __ge__(self, other):
            if not isinstance(other, OldSolc.SemVerVersion):
                return False
            return self == other or self > other

        def lower(self):
            return OldSolc.SemVerVersion([v if v is not None else self.MIN_DIGIT_VALUE for v in self.version])

        def upper(self):
            return OldSolc.SemVerVersion([v if v is not None else self.MAX_DIGIT_VALUE for v in self.version])

    class SemVerRange:
        def __init__(self, lower, upper, lower_inclusive=True, upper_inclusive=True):
            self.lower = lower
            self.upper = upper
            self.lower_inclusive = lower_inclusive
            self.upper_inclusive = upper_inclusive

        def __str__(self):
            return f"{{SemVerRange: {self.lower} <{'=' if self.upper_inclusive else ''} Version <{'=' if self.upper_inclusive else ''} {self.upper}}}"

        def constrain(self, other):
            low, high, low_inc, high_inc = self.lower, self.upper, self.lower_inclusive, self.upper_inclusive
            if other.lower > low or (other.lower == low and not other.lower_inclusive):
                low = other.lower
                low_inc = other.lower_inclusive
            if other.upper < high or (other.upper == high and not other.upper_inclusive):
                high = other.upper
                high_inc = other.upper_inclusive
            return OldSolc.SemVerRange(low, high, low_inc, high_inc)


    @property
    def max_version(self):
        return OldSolc.SemVerVersion([OldSolc.SemVerVersion.MAX_DIGIT_VALUE] * 3)

    @property
    def min_version(self):
        return OldSolc.SemVerVersion([OldSolc.SemVerVersion.MIN_DIGIT_VALUE] * 3)

    @staticmethod
    def _parse_version(version):
        """
        Returns a 3-item array where each item is [major, minor, patch] version.
            -Either each number is an integer, or if it is a wildcard, it is None.
        :param version: The semver version string to parse.
        :return: The resulting SemVerVersion which represents major, minor and patch revisions.
        """

        # Match the version pattern.
        match = OldSolc.CAPTURING_VERSION_PATTERN.findall(version)

        # If there was no matches (or more than one) the format is irregular, so we return None.
        if not match or len(match) > 1:
            return None

        # Filter all blank groups out.
        match = [int(y) if y.isdigit() else None for x in match for y in x if y]

        # Extend the array to a length of 3 and return it.
        original_length = len(match)
        match += [0] * max(0, 3 - original_length)
        return OldSolc.SemVerVersion(match, original_length)

    def _get_range(self, operation, version):

        # Assert our version state
        assert version.original_length > 0, "Original version should specify at least one digit"

        # Handle our range based off of operation type.
        if operation in [None, "", "=", "v"]:
            return OldSolc.SemVerRange(version.lower(), version.upper())
        elif operation == ">":
            return OldSolc.SemVerRange(version.upper(), self.max_version, False, True)
        elif operation == ">=":
            return OldSolc.SemVerRange(version.upper(), self.max_version, True, True)
        elif operation == "<":
            return OldSolc.SemVerRange(self.min_version, version.lower(), True, False)
        elif operation == "<=":
            return OldSolc.SemVerRange(self.min_version, version.lower(), True, True)
        elif operation == "~":
            # Patch-level changes if minor version was defined, minor-level changes otherwise.
            low = version.lower()
            high = version.upper()

            # Determine which index we should increment based off how many were specified.
            increment_index = 0 if version.original_length == 1 else 1

            # Increment the significant version digit and zero out the following ones.
            high.version[increment_index] += 1
            for i in range(increment_index + 1, len(high.version)):
                high.version[i] = 0

            # Our result is an exclusive upper bound, and inclusive lower.
            return OldSolc.SemVerRange(low, high, True, False)

        elif operation == "^":
            # The upper bound is determined by incrementing the first non-zero digit from left, and zeroing out all
            # following digits.
            low = version.lower()
            high = version.upper()

            # Determine the first significant digit (non-zero) from left.
            digit_index = len(high.version) - 1
            for i in range(0, len(high.version)):
                if high.version[i] != 0:
                    digit_index = i
                    break

            # Increment the digit and zero out all following digits.
            high.version[digit_index] += 1
            for i in range(digit_index + 1, len(high.version)):
                high.version[i] = 0

            # Our result is an exclusive upper bound, and inclusive lower.
            return OldSolc.SemVerRange(low, high, True, False)

    def _is_allowed_pragma(self, version):
        """
        Determines if a given version pragma is allowed (not outdated).
        :param version: The version string to check Solidity's semver is satisfied.
        :return: Returns True if the version is allowed, False otherwise.
        """

        # TODO: Sanitize the version string so it only contains the portions after the "solidity" text. This is
        # already the case in this environment, but maybe other solidity versions differ? Verify this.

        # First we parse the overall pragma statement, which could have multiple spec items in it (> x, <= y, etc).
        spec_items = self.SPEC_PATTERN.findall(version)

        # If we don't have any items, we return the appropriate error
        if not spec_items:
            # TODO: Return an error that the pragma was malformed or untraditional.
            return False

        # Loop for each spec item, of which there are two kinds:
        # (1) <operator><version> (standard)
        # (2) <version1> - <version2> (range)
        result_range = None
        for spec_item in spec_items:

            # Skip any results that don't have 5 items (to be safe)
            if len(spec_item) < 5:
                continue

            # If the first item exists, it's case (1)
            if spec_item[0]:
                # This is a range specified by a standard operation applied on a version.
                operation, version = spec_item[0], self._parse_version(spec_item[1])
                spec_range = self._get_range(operation, version)
            else:
                # This is a range from a lower bound to upper bound.
                version_lower, operation, version_higher = self._parse_version(spec_item[2]), spec_item[3], \
                                                           self._parse_version(spec_item[4])
                spec_range = OldSolc.SemVerRange(version_lower.lower(), version_higher.upper(), True, True)

            # Constrain our range further.
            if result_range is None:
                result_range = spec_range
            else:
                result_range = result_range.constrain(spec_range)

        # Parse the newest disallowed version, and determine if we fall into the lower bound.
        newest_disallowed = self._parse_version(self.DISALLOWED_THRESHOLD)

        self.log(f"FINAL RANGE: {result_range}\n")
        if result_range.lower_inclusive:
            return newest_disallowed < result_range.lower
        else:
            return newest_disallowed <= result_range.lower


    def tests(self):
        # TODO: Remove this once all testing is complete.
        # Basic equality
        spec_range = self._get_range("", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == "0.4.23" and str(spec_range.upper) == "0.4.23" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is True
        spec_range = self._get_range("=", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == "0.4.23" and str(spec_range.upper) == "0.4.23" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is True
        spec_range = self._get_range("v", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == "0.4.23" and str(spec_range.upper) == "0.4.23" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is True
        spec_range = self._get_range(">", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == "0.4.23" and str(spec_range.upper) == str(self.max_version) and spec_range.lower_inclusive is False and spec_range.upper_inclusive is True
        spec_range = self._get_range(">=", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == "0.4.23" and str(spec_range.upper) == str(self.max_version) and spec_range.lower_inclusive is True and spec_range.upper_inclusive is True
        spec_range = self._get_range("<", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == str(self.min_version) and str(spec_range.upper) == "0.4.23" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("<=", self._parse_version("0.4.23"))
        assert str(spec_range.lower) == str(self.min_version) and str(spec_range.upper) == "0.4.23" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is True
        # Tilda
        spec_range = self._get_range("~", self._parse_version("1.2.3"))
        assert str(spec_range.lower) == "1.2.3" and str(spec_range.upper) == "1.3.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("~", self._parse_version("1.2"))
        assert str(spec_range.lower) == "1.2.0" and str(spec_range.upper) == "1.3.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("~", self._parse_version("1"))
        assert str(spec_range.lower) == "1.0.0" and str(spec_range.upper) == "2.0.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("~", self._parse_version("0.2.3"))
        assert str(spec_range.lower) == "0.2.3" and str(spec_range.upper) == "0.3.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("~", self._parse_version("0.2"))
        assert str(spec_range.lower) == "0.2.0" and str(spec_range.upper) == "0.3.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("~", self._parse_version("0"))
        assert str(spec_range.lower) == "0.0.0" and str(spec_range.upper) == "1.0.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        # Caret
        spec_range = self._get_range("^", self._parse_version("1.2.3"))
        assert str(spec_range.lower) == "1.2.3" and str(spec_range.upper) == "2.0.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("^", self._parse_version("0.2.3"))
        assert str(spec_range.lower) == "0.2.3" and str(spec_range.upper) == "0.3.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("^", self._parse_version("0.0.3"))
        assert str(spec_range.lower) == "0.0.3" and str(spec_range.upper) == "0.0.4" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False

        # Caret-Special Cases
        spec_range = self._get_range("^", self._parse_version("1.2.x"))
        assert str(spec_range.upper) == "2.0.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False
        spec_range = self._get_range("^", self._parse_version("0.0.x"))
        assert str(spec_range.upper) == "0.1.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False, spec_range
        spec_range = self._get_range("^", self._parse_version("0.0"))
        assert str(spec_range.lower) == "0.0.0" and str(spec_range.upper) == "0.1.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False, spec_range

        # Caret-Special Cases 2
        spec_range = self._get_range("^", self._parse_version("1.x"))
        assert str(spec_range.lower) == "1.0.0" and str(spec_range.upper) == "0.1.0" and spec_range.lower_inclusive is True and spec_range.upper_inclusive is False, spec_range

    def detect(self):
        # TODO: Remove this once all testing is complete.
        self.tests()
        results = []
        pragma = self.slither.pragma_directives
        old_pragma = sorted([p for p in pragma if not self._is_allowed_pragma(p.version)], key=lambda x:str(x))

        if old_pragma:
            info = "Old version (<0.4.23) of Solidity allowed in {}:\n".format(self.filename)
            for p in old_pragma:
                info += "\t- {} declares {}\n".format(p.source_mapping_str, str(p))
            self.log(info)

            json = self.generate_json_result(info)
            # follow the same format than add_nodes_to_json
            json['expressions'] = [{'expression': p.version,
                                    'source_mapping': p.source_mapping} for p in old_pragma]
            results.append(json)

        return results
