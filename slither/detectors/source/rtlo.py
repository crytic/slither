from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re

from slither.utils import json_utils


class RightToLeftOverride(AbstractDetector):
    """
    Detect the usage of a Right-To-Left-Override (U+202E) character
    """

    ARGUMENT = 'rtlo'
    HELP = 'Right-To-Left-Override control character is used'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#right-to-left-override-character'
    WIKI_TITLE = 'Right-To-Left-Override character'
    WIKI_DESCRIPTION = 'An attacker can manipulate the logic of the contract by using a right-to-left-override character (U+202E)'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Token
{

    address payable o; // owner
    mapping(address => uint) tokens;

    function withdraw() external returns(uint)
    {
        uint amount = tokens[msg.sender];
        address payable d = msg.sender;
        tokens[msg.sender] = 0;
        _withdraw(/*owner‮/*noitanitsed*/ d, o/*‭
		        /*value */, amount);
    }

    function _withdraw(address payable fee_receiver, address payable destination, uint value) internal
    {
		fee_receiver.transfer(1);
		destination.transfer(value);
    }
}
```

`Token` uses the right-to-left-override character when calling `_withdraw`. As a result, the fee is incorrectly sent to `msg.sender`, and the token balance is sent to the owner.

'''
    WIKI_RECOMMENDATION = 'Special control characters must not be allowed.'

    RTLO_CHARACTER_ENCODED = "\u202e".encode('utf-8')

    def _detect(self):
        results = []
        pattern = re.compile(".*\u202e.*".encode('utf-8'))

        for filename, source in self.slither.source_code.items():
            # Attempt to find all RTLO characters in this source file.
            original_source_encoded = source.encode('utf-8')
            start_index = 0

            # Keep searching all file contents for the character.
            while True:
                source_encoded = original_source_encoded[start_index:]
                result_index = source_encoded.find(self.RTLO_CHARACTER_ENCODED)

                # If we couldn't find the character in the remainder of source, stop.
                if result_index == -1:
                    break
                else:
                    # We found another instance of the character, define our output
                    idx = start_index + result_index
                    info = f"{filename} contains a unicode right-to-left-override character at byte offset {idx}:\n"

                    # We have a patch, so pattern.find will return at least one result

                    info += f"\t- {pattern.findall(source_encoded)[0]}\n"
                    json = self.generate_json_result(info)
                    json_utils.add_other_to_json("rtlo-character",
                                                 (filename, idx, len(self.RTLO_CHARACTER_ENCODED)),
                                                 json,
                                                 self.slither)
                    results.append(json)

                    # Advance the start index for the next iteration
                    start_index = result_index + 1

        return results
