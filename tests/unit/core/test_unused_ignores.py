import os
import tempfile
from pathlib import Path

from slither import Slither
from slither.detectors.naming_convention.naming_convention import NamingConvention

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
UNUSED_IGNORES_TEST_DATA_DIR = Path(TEST_DATA_DIR, "unused_ignores")


def test_unused_ignore_detection(solc_binary_path) -> None:
    """Test that unused slither-disable comments are detected correctly."""
    solc_path = solc_binary_path("0.8.10")
    slither = Slither(
        Path(UNUSED_IGNORES_TEST_DATA_DIR, "unused_ignores.sol").as_posix(), solc=solc_path
    )

    # Enable unused ignore tracking
    slither.warn_unused_ignores = True

    # Register and run the naming-convention detector to trigger some disable comments
    slither.register_detector(NamingConvention)
    slither.run_detectors()

    # Get unused ignore comments
    unused = slither.get_unused_ignore_comments()

    # Check that we found some unused ignores
    assert len(unused) > 0, "Expected to find unused ignore comments"

    # Verify specific unused detectors are reported
    unused_detectors = set()
    for item in unused:
        unused_detectors.update(item["unused_detectors"])

    # reentrancy-eth should be reported as unused since the naming-convention
    # detector doesn't find any reentrancy
    assert "reentrancy-eth" in unused_detectors, "Expected reentrancy-eth to be unused"


def test_all_ignores_used(solc_binary_path) -> None:
    """Test that when all ignore comments are used, none are reported as unused."""
    solc_path = solc_binary_path("0.8.10")

    # Create a simple test with slither-disable for a detector that will be triggered
    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract AllUsed {
    // slither-disable-next-line naming-convention
    uint public Bad_Name;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "all_used.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        slither.warn_unused_ignores = True

        # Register and run the naming-convention detector
        slither.register_detector(NamingConvention)
        slither.run_detectors()

        # Get unused ignore comments
        unused = slither.get_unused_ignore_comments()

        # naming-convention should NOT be in unused since it was triggered
        for item in unused:
            assert "naming-convention" not in item["unused_detectors"], (
                "naming-convention should be used, not unused"
            )


def test_parse_ignore_comments_tracking(solc_binary_path) -> None:
    """Test that ignore comments are properly tracked during parsing."""
    solc_path = solc_binary_path("0.8.10")
    slither = Slither(
        Path(UNUSED_IGNORES_TEST_DATA_DIR, "unused_ignores.sol").as_posix(), solc=solc_path
    )

    # Check that _all_ignore_comments is populated
    all_comments = slither._all_ignore_comments
    assert len(all_comments) > 0, "Expected ignore comments to be tracked"

    # Find the test file in the comments
    test_file_found = False
    for file_path in all_comments:
        if "unused_ignores.sol" in file_path:
            test_file_found = True
            comments = all_comments[file_path]
            # Should have multiple ignore comments
            assert len(comments) >= 4, "Expected at least 4 ignore comments in test file"

            # Check comment types
            comment_types = set(c[1] for c in comments)
            assert "next-line" in comment_types, "Expected next-line comments"
            assert "start" in comment_types, "Expected start comments"

    assert test_file_found, "Test file not found in ignore comments"


def test_empty_detector_list_not_tracked(solc_binary_path) -> None:
    """Test that empty detector lists (// slither-disable-next-line) are not tracked."""
    solc_path = solc_binary_path("0.8.10")

    # Create a test with an empty detector list
    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract EmptyDetector {
    // slither-disable-next-line
    uint public x;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "empty_detector.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)

        # Find comments for this file
        for file_path in slither._all_ignore_comments:
            if "empty_detector.sol" in file_path:
                for line, comment_type, detectors in slither._all_ignore_comments[file_path]:
                    # Ensure no empty strings in detectors
                    assert "" not in detectors, "Empty detector string should not be tracked"


def test_whitespace_in_detector_list_handled(solc_binary_path) -> None:
    """Test that whitespace in detector lists is properly stripped."""
    solc_path = solc_binary_path("0.8.10")

    # Create a test with whitespace in detector list
    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract WhitespaceTest {
    // slither-disable-next-line naming-convention , reentrancy-eth
    uint public Bad_Name;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "whitespace_test.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        slither.warn_unused_ignores = True

        slither.register_detector(NamingConvention)
        slither.run_detectors()

        # Verify naming-convention was tracked and used (no whitespace issues)
        unused = slither.get_unused_ignore_comments()
        for item in unused:
            # naming-convention should not appear as unused since it was triggered
            assert "naming-convention" not in item["unused_detectors"], (
                "naming-convention should be used"
            )


def test_all_keyword_used(solc_binary_path) -> None:
    """Test that the 'all' keyword properly marks comments as used."""
    solc_path = solc_binary_path("0.8.10")

    # Create a test with 'all' keyword
    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract AllKeyword {
    // slither-disable-next-line all
    uint public Bad_Name;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "all_keyword.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        slither.warn_unused_ignores = True

        slither.register_detector(NamingConvention)
        slither.run_detectors()

        # 'all' should be marked as used since naming-convention was triggered
        unused = slither.get_unused_ignore_comments()
        for item in unused:
            assert "all" not in item["unused_detectors"], (
                "'all' should be used since a detector was triggered"
            )


DEPENDENCY_WITH_USED_IGNORE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract Dep {
    // slither-disable-next-line naming-convention
    uint public Bad_Name;
}
"""

DEPENDENCY_WITH_UNUSED_IGNORE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract Dep {
    // slither-disable-next-line reentrancy-eth
    uint public goodName;
}
"""

MAIN_IMPORTING_DEPENDENCY = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "./lib/Dep.sol";

contract Main is Dep {
    uint public value;
}
"""


def _unused_ignores_with_dependency(
    solc_path: str, dependency_source: str, **path_filters: list[str]
) -> list[dict]:
    """Run naming-convention on Main.sol, which imports lib/Dep.sol, and return unused ignores."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "lib"))
        with open(os.path.join(tmpdir, "lib", "Dep.sol"), "w") as f:
            f.write(dependency_source)
        main_file = os.path.join(tmpdir, "Main.sol")
        with open(main_file, "w") as f:
            f.write(MAIN_IMPORTING_DEPENDENCY)

        slither = Slither(main_file, solc=solc_path, **path_filters)
        slither.warn_unused_ignores = True
        slither.register_detector(NamingConvention)
        slither.run_detectors()
        return slither.get_unused_ignore_comments()


def test_unused_ignores_without_path_filters_reports_dependency(solc_binary_path) -> None:
    """Without path filters, an unused directive in an imported file is still reported."""
    unused = _unused_ignores_with_dependency(
        solc_binary_path("0.8.10"), DEPENDENCY_WITH_UNUSED_IGNORE
    )

    assert {(Path(item["file"]).name, tuple(item["unused_detectors"])) for item in unused} == {
        ("Dep.sol", ("reentrancy-eth",))
    }


def test_filter_paths_skips_used_ignore_in_filtered_file(solc_binary_path) -> None:
    """A directive that suppresses a finding in a filtered path is not reported as unused."""
    unused = _unused_ignores_with_dependency(
        solc_binary_path("0.8.10"), DEPENDENCY_WITH_USED_IGNORE, filter_paths=["lib"]
    )

    assert unused == []


def test_filter_paths_skips_unused_ignore_in_filtered_file(solc_binary_path) -> None:
    """Unused directives in a filtered path are not reported."""
    unused = _unused_ignores_with_dependency(
        solc_binary_path("0.8.10"), DEPENDENCY_WITH_UNUSED_IGNORE, filter_paths=["lib"]
    )

    assert unused == []


def test_include_paths_skips_ignores_outside_included_paths(solc_binary_path) -> None:
    """Directives in files outside include_paths are not reported."""
    unused = _unused_ignores_with_dependency(
        solc_binary_path("0.8.10"), DEPENDENCY_WITH_UNUSED_IGNORE, include_paths=["Main.sol"]
    )

    assert unused == []


def test_include_paths_still_reports_ignores_in_included_paths(solc_binary_path) -> None:
    """Directives in files matched by include_paths are still reported."""
    unused = _unused_ignores_with_dependency(
        solc_binary_path("0.8.10"), DEPENDENCY_WITH_UNUSED_IGNORE, include_paths=["lib"]
    )

    assert {(Path(item["file"]).name, tuple(item["unused_detectors"])) for item in unused} == {
        ("Dep.sol", ("reentrancy-eth",))
    }
