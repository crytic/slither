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
    SPEC_PATTERN = re.compile(f"(?:(?:(\^|\~|\>\s*=|\<\s*\=|\<|\>|\=|v)\s*({VERSION_PATTERN}))|(?:\s*({VERSION_PATTERN})\s*(\-)\s*({VERSION_PATTERN})\s*))(\s*\|\|\s*|\s*)")

    # Indicates the highest disallowed version.
    DISALLOWED_THRESHOLD = "0.4.22"

    class SemVerVersion(object):
        """
        Represents a version in semver. Wildcards are supported.
        """
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
        """
        Represents a range of versions supported in semver.
        """
        def __init__(self, lower, upper, lower_inclusive=True, upper_inclusive=True):
            self.lower = lower
            self.upper = upper
            self.lower_inclusive = lower_inclusive
            self.upper_inclusive = upper_inclusive

        def __str__(self):
            return f"{{SemVerRange: {self.lower} <{'=' if self.upper_inclusive else ''} Version <{'=' if self.upper_inclusive else ''} {self.upper}}}"

        def intersection(self, other):
            """
            Performs an intersection operation on both ranges.
            :param other: The other SemVerRange to perform the intersection with.
            :return: Returns a SemVerRange which is the intersection of this and the other range provided.
            """
            low, high, low_inc, high_inc = self.lower, self.upper, self.lower_inclusive, self.upper_inclusive
            if other.lower > low or (other.lower == low and not other.lower_inclusive):
                low = other.lower
                low_inc = other.lower_inclusive
            if other.upper < high or (other.upper == high and not other.upper_inclusive):
                high = other.upper
                high_inc = other.upper_inclusive
            return OldSolc.SemVerRange(low, high, low_inc, high_inc)

        @property
        def is_valid(self):
            """
            Indicates whether the range can encapsulate any values.
            :return: Returns True if the range can encapsulate any possible value, False if it is an invalid range.
            """
            return self.lower < self.upper or \
                   (self.lower == self.upper and (self.lower_inclusive or self.upper_inclusive))


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
        """
        Obtains a SemVerRange given an operation and version (a single spec item).
        :param operation: A string (typically single char) denoting the operation to perform on the provided version.
        :param version: The version string to perform an operation on to obtain a range.
        :return: Returns a SemVerRange that represents the range of values yielded from the given operation.
        """
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
                if version.original_length < i + 1 or version.version[i] is None:
                    digit_index = max(0, i - 1)
                    break
                if high.version[i] != 0:
                    digit_index = i
                    break

            # Increment the digit and zero out all following digits.
            high.version[digit_index] += 1
            for i in range(digit_index + 1, len(high.version)):
                high.version[i] = 0

            # Our result is an exclusive upper bound, and inclusive lower.
            return OldSolc.SemVerRange(low, high, True, False)

    def _is_disallowed_pragma(self, version):
        """
        Determines if a given version pragma is allowed (not outdated).
        :param version: The version string to check Solidity's semver is satisfied.
        :return: Returns a string with a reason why the pragma is disallowed, or returns None if it is valid.
        """

        # First we parse the overall pragma statement, which could have multiple spec items in it (> x, <= y, etc).
        spec_items = self.SPEC_PATTERN.findall(version)

        # If we don't have any items, we return the appropriate error
        if not spec_items:
            return f"Untraditional or complex version spec"

        # Loop for each spec item, of which there are two kinds:
        # (1) <operator><version_operand> (standard)
        # (2) <version1> - <version2> (range)
        result_ranges = []
        intersecting = False  # True if this is an AND operation, False if it is an OR operation.
        for spec_item in spec_items:

            # Skip any results that don't have 5 items (to be safe)
            if len(spec_item) < 6:
                continue

            # If the first item exists, it's case (1)
            if spec_item[0]:
                # This is a range specified by a standard operation applied on a version.
                operation, version_operand = spec_item[0], self._parse_version(spec_item[1])
                spec_range = self._get_range(operation, version_operand)
            else:
                # This is a range from a lower bound to upper bound.
                version_lower, operation, version_higher = self._parse_version(spec_item[2]), spec_item[3], \
                                                           self._parse_version(spec_item[4])
                spec_range = OldSolc.SemVerRange(version_lower.lower(), version_higher.upper(), True, True)

            # If we have no items, or we are performing a union, we simply add the range to our list
            if len(result_ranges) == 0 or not intersecting:
                result_ranges.append(spec_range)
            else:
                # If we are intersecting, we only intersect with the most recent versions.
                result_ranges[-1] = result_ranges[-1].intersection(spec_range)

            # Set our operation (AND/OR) from the captured end of this.
            intersecting = "||" not in spec_item[5]

        # Parse the newest disallowed version, and determine if we fall into the lower bound.
        newest_disallowed = self._parse_version(self.DISALLOWED_THRESHOLD)

        # Verify any range doesn't allow as old or older than our newest disallowed.
        valid_ranges = 0
        for result_range in result_ranges:

            # Skip any invalid ranges that would allow no versions through.
            if not result_range.is_valid:
                continue

            # Increment our valid ranges.
            valid_ranges += 1

            # We now know this range allows some values through. If it's lower bound is less than the newest disallowed,
            # then it lets through the newest disallowed, or some lower values.
            if (result_range.lower_inclusive and newest_disallowed >= result_range.lower) \
                    or newest_disallowed > result_range.lower:
                return f"Version spec allows old versions of solidity (<={self.DISALLOWED_THRESHOLD})"

        # Verify we did allow some valid range of versions through.
        if valid_ranges == 0:
            return "Version spec does not allow any valid range of versions"
        else:
            return None

    def detect(self):
        """
        Detects pragma statements that allow for outdated solc versions.
        :return: Returns the relevant JSON data for the findings.
        """
        # Detect all version related pragmas and check if they are disallowed.
        results = []
        pragma = self.slither.pragma_directives
        disallowed_pragmas = []
        detected_version = False
        for p in pragma:
            # Skip any pragma directives which do not refer to version
            if len(p.directive) < 1 or p.directive[0] != "solidity":
                continue

            # This is version, so we test if this is disallowed.
            detected_version = True
            reason = self._is_disallowed_pragma(p.version)
            if reason:
                disallowed_pragmas.append((reason, p))

        # If we found any disallowed pragmas, we output our findings.
        if disallowed_pragmas:
            info = "Detected issues with version pragma in {}:\n".format(self.filename)
            for (reason, p) in disallowed_pragmas:
                info += "\t- {} ({})\n".format(reason, p.source_mapping_str)
            self.log(info)

            json = self.generate_json_result(info)

            # follow the same format than add_nodes_to_json
            json['expressions'] = [{'expression': p.version,
                                    'source_mapping': p.source_mapping} for (reason, p) in disallowed_pragmas]
            results.append(json)

        # If we never detected a version-related pragma statement, output an error.
        elif not detected_version:
            # If we had no pragma statements, we warn the user that no version spec was included in this file.
            info = "No version pragma detected in {}\n".format(self.filename)
            self.log(info)

            json = self.generate_json_result(info)
            results.append(json)

        return results
