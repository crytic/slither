from slither.detectors.reentrancy.reentrancy_events import ReentrancyEvent


def test_event_call_sites_have_stable_order(slither_from_solidity_source, monkeypatch):
    source = """
    contract C {
        event E();
        function emitEvent() internal { emit E(); }
        function f(address target, bool choice) external {
            target.call("");
            if (choice) { emitEvent(); } else { emitEvent(); }
        }
    }
    """
    with slither_from_solidity_source(source) as slither:
        detector = ReentrancyEvent(slither.compilation_units[0], slither, None)
        detector._detect()
        findings = detector.find_reentrancies()
        assert len(findings) == 1
        key, events = next(iter(findings.items()))
        assert len(events) == 2
        events = sorted(events, key=lambda event: event.nodes[-1].source_mapping.start)
        outputs = []
        for ordered_events in (events, list(reversed(events))):
            # Exercise both possible orders at the identity-hashed set boundary.
            monkeypatch.setattr(
                detector,
                "find_reentrancies",
                lambda ordered_events=ordered_events: {key: ordered_events},
            )
            outputs.append(detector._detect()[0].data)
        assert outputs[0] == outputs[1]
        event_elements = [
            element
            for element in outputs[0]["elements"]
            if element.get("additional_fields", {}).get("underlying_type") == "event"
        ]
        assert len(event_elements) == 4
