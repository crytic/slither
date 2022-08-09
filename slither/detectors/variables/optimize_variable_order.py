from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import itertools

class OtimizeVariableOrder(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = "optimize-var-order"
    HELP = "Find space optimizations from reordering variables"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/Optimizing-variable-order-detector"

    WIKI_TITLE = "Optimal Variable Order Detector"
    WIKI_DESCRIPTION = (
        "Detect optimizations in the variable order of structs to decrease the number of slots used"
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    struct original {
        uint128 a
        uint256 b
        uint128 c
    }
```
A struct is declared with an unoptimized variable order. The `original` struct will take 3 stroage slots because each variable will have its own slot."""
    WIKI_RECOMMENDATION = """
```solidity
    struct optimized {
        uint128 a
        uint128 c
        uint256 b
    }
```
The struct's variables are reordered to take advantage of Solidity's variable packing. The struct's variables `a` and `b` will both be packed into the same slot, resulting in the `optimized` struct only taking 2 storage slots."""
      
    BYTES_PER_SLOT = 32

    @staticmethod
    def find_slots_used(elem_order):
        """returns the number of slots the current element order in @elem_order uses"""
        slot_count = 0
        slot_bytes_used = 0
        for elem in elem_order:
            if elem.type.storage_size[0] <= (OtimizeVariableOrder.BYTES_PER_SLOT - slot_bytes_used):
                # room in current slot
                slot_bytes_used += elem.type.storage_size[0]
            else:
                # new slot
                slot_count += 1
                slot_bytes_used = elem.type.storage_size[0]

        # if used any bits of next slot, need all of new slot
        if slot_bytes_used > 0:
            slot_count += 1

        return slot_count

    @staticmethod
    def find_smallest_pack_order(target_elems):
        """finds smallest packed size order of @target_elems. 
        Currently uses dirty O(n^2) by finding minimum by trying all order combos"""
        smallest_pack_order = target_elems[:]
        smallest_pack_order_slots =  OtimizeVariableOrder.find_slots_used(smallest_pack_order)

        for possible_smallest in itertools.permutations(target_elems):
            if OtimizeVariableOrder.find_slots_used(possible_smallest) < \
                OtimizeVariableOrder.find_slots_used(smallest_pack_order):
                # change smallest order
                smallest_pack_order = possible_smallest[:]
                smallest_pack_order_slots = OtimizeVariableOrder.find_slots_used(possible_smallest)
        
        return smallest_pack_order

    @staticmethod
    def find_optimized_struct_ordering(target_struct):
        """returns an optimized version of @target_struct or None if there's no better optimization"""

        packable_vars = []
        unpackable_vars = []
        for elem in target_struct.elems_ordered:
            if elem.type.storage_size[0] < OtimizeVariableOrder.BYTES_PER_SLOT:
                packable_vars.append(elem)
            else:
                unpackable_vars.append(elem)

        if len(packable_vars) < 2:
            # no way can pack anything
            return None

        best_packable_order = OtimizeVariableOrder.find_smallest_pack_order(packable_vars)
        best_packable_order += tuple(unpackable_vars) # add unpackable elements at the end

        if OtimizeVariableOrder.find_slots_used(best_packable_order) < \
            OtimizeVariableOrder.find_slots_used(target_struct.elems_ordered):
            return best_packable_order
        else:
            return None

    def _detect(self):
        optimized_structs_pair = []

        for contract in self.compilation_unit.contracts_derived:
            for struct in contract.structures:
                if optimized_struct := OtimizeVariableOrder.find_optimized_struct_ordering(struct):
                    optimized_structs_pair.append([struct.elems_ordered, optimized_struct])

        print("--------------")
        print("optimized_structs:")
        for pair in optimized_structs_pair:
            original, optimzed = pair
            print(f"original struct (size: {OtimizeVariableOrder.find_slots_used(original)}):")
            print("{")
            for e in original:
                print(f"\t{e.type} {e.name}")
            print("}")

            print(f"optimized struct (size: {OtimizeVariableOrder.find_slots_used(optimzed)}):")
            print("{")
            for e in optimzed:
                print(f"\t{e.type} {e.name}")
            print("}")
            print("---")
        print("--------------")
            
        info = ["idk what to put here :)"]
        res = self.generate_result(info)

        return [res]
