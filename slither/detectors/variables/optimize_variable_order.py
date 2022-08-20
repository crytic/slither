from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import itertools

class OptimizeVariableOrder(AbstractDetector):
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
        """
        returns the number of slots @elem_order uses
        calculated per https://docs.soliditylang.org/en/v0.8.15/internals/layout_in_storage.html#layout-of-state-variables-in-storage

        rules:
        1. The first item in a storage slot is stored lower-order aligned.

        2. Value types use only as many bytes as are necessary to store them.

        3. If a value type does not fit the remaining part of a storage slot, it is stored in the next storage slot.

        4. Structs and array data always start a new slot and their items are packed tightly according to these rules.

        5. Items following struct or array data always start a new storage slot.

        reminder:
        storage_size[0] = size in bytes
        storage_size[1] = if forced to have own storage spot
        """
        
        slot_count = 0
        slot_bytes_used = 0
        for i, elem in enumerate(elem_order):
            # rule 5 or 3 or 4
            if (i != 0 and elem_order[i-1].type.storage_size[1]) or \
                elem.type.storage_size[1] or \
                elem.type.storage_size[0] > (OptimizeVariableOrder.BYTES_PER_SLOT - slot_bytes_used):
                # need own slot

                if slot_bytes_used == 0:
                    # slot is empty, just use this one
                    slot_bytes_used = elem.type.storage_size[0]
                else:
                    # new slot
                    slot_count += 1
                    slot_bytes_used = elem.type.storage_size[0]
            else:                
                # pack into current slot
                slot_bytes_used += elem.type.storage_size[0]

        # if used any bits of current slot, need all of new slot
        if slot_bytes_used > 0:
            slot_count += 1

        return slot_count

    @staticmethod
    def find_smallest_pack_order(target_elems):
        """
        Finds smallest packed size order of @target_elems. Note: asumes none of the elements need their own slot

        This is a "Bin Packing" problem and a First Fit Decreasing algorithm is used.
        More information: https://en.wikipedia.org/wiki/First-fit-decreasing_bin_packing
        """
                
        if len(target_elems) < 2:
            # packing order doesn't matter
            return target_elems

         # biggest first, acc to storage size
        target_elems.sort(reverse=True, key=lambda x: x.type.storage_size[0])

        slots = []

        for elem in target_elems:
            for slot in slots:
                if (slot["sum"] + elem.type.storage_size[0]) \
                     <= OptimizeVariableOrder.BYTES_PER_SLOT:
                     # add to this slot
                     slot["vars"].append(elem)
                     slot["sum"] += elem.type.storage_size[0]
                     break
            else:
                # didn't 'break' from loop. Create new slot
                slots.append({"sum": elem.type.storage_size[0], "vars": [elem]})
        
        optimized_order = []
        for s in slots:
            optimized_order += s["vars"]
        return optimized_order

    @staticmethod
    def find_optimized_struct_ordering(target_struct):
        """returns an optimized version of @target_struct or None if there isn't a better optimization"""

        if len(target_struct) < 2:
            # packing order doesn't matter. Nothing to optimize
            return None
        
        # preprocessing elements to ensure only re-ordering elements that can result in optimizations
        packable_vars = []
        unpackable_vars = []
        for elem in target_struct.elems_ordered:
            if not elem.type.storage_size[1] and \
                elem.type.storage_size[0] < OptimizeVariableOrder.BYTES_PER_SLOT:
                packable_vars.append(elem)
            else:
                unpackable_vars.append(elem)

        best_packable_order = OptimizeVariableOrder.find_smallest_pack_order(packable_vars)
        best_packable_order += tuple(unpackable_vars) # add unpackable elements at the end
        if OptimizeVariableOrder.find_slots_used(best_packable_order) < \
            OptimizeVariableOrder.find_slots_used(target_struct.elems_ordered):
            return best_packable_order
        else:
            return None

    def _detect(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for struct in contract.structures:
                if optimized_struct := OptimizeVariableOrder.find_optimized_struct_ordering(struct):
                    info = [f"Optimization opportunity in contract {struct.canonical_name}:\n"]
                    info += [f"\toriginal {struct.canonical_name} struct (size: ", \
                        str(OptimizeVariableOrder.find_slots_used(struct.elems_ordered))," slots)\n"]
                    info += ["\t{\n"]
                    for e in struct.elems_ordered:
                        info += [f"\t\t {e.type} {e.name}\n"]
                    info += ["\t}\n"]
                    info += [f"\toptimized {struct.canonical_name} struct (size: ", \
                        str(OptimizeVariableOrder.find_slots_used(optimized_struct))," slots)\n"]
                    info += ["\t{\n"]
                    for e in optimized_struct:
                        info += [f"\t\t {e.type} {e.name}\n"]
                    info += ["\t}\n"]

                    res = self.generate_result(info)

                    results.append(res)
            
        return results
