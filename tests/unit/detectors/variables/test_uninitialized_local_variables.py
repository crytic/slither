from slither.detectors.variables.uninitialized_local_variables import UninitializedLocalVars


def test_findings_have_source_order(slither_from_solidity_source):
    declarations = " ".join(f"uint v{index};" for index in range(8))
    expression = " + ".join(f"v{index}" for index in range(8))
    source = (
        "contract C { function f() external pure returns (uint) { "
        f"{declarations} return {expression}; "
        "} }"
    )
    with slither_from_solidity_source(source) as slither:
        detector = UninitializedLocalVars(slither.compilation_units[0], slither, None)
        results = detector._detect()
        assert [result.data["elements"][0]["name"] for result in results] == [
            f"v{index}" for index in range(8)
        ]
