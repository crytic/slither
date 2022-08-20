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
    def find_optimized_struct_ordering(target_collection_elems):
        """returns an optimized version of @target_collection_elems or None if there isn't a better optimization"""

        if len(target_collection_elems) < 2:
            # packing order doesn't matter. Nothing to optimize
            return None
        
        # preprocessing elements to ensure only re-ordering elements that can result in optimizations
        packable_vars = []
        unpackable_vars = []
        for elem in target_collection_elems:
            if not elem.type.storage_size[1] and \
                elem.type.storage_size[0] < OptimizeVariableOrder.BYTES_PER_SLOT:
                packable_vars.append(elem)
            else:
                unpackable_vars.append(elem)

        best_packable_order = OptimizeVariableOrder.find_smallest_pack_order(packable_vars)
        best_packable_order += tuple(unpackable_vars) # add unpackable elements at the end
        if OptimizeVariableOrder.find_slots_used(best_packable_order) < \
            OptimizeVariableOrder.find_slots_used(target_collection_elems):
            return best_packable_order
        else:
            return None

    def _detect(self):
        results = []

        # file & contract-specific structs, contract-specific storage vars
        # format: [("description/location", [elements...]), ...]
        all_var_collections = [] 

        for top_level_struct in self.compilation_unit.structures_top_level:
            all_var_collections.append((\
                f"struct {top_level_struct.canonical_name} ({top_level_struct.source_mapping})",\
                     top_level_struct.elems_ordered))

        for contract in self.compilation_unit.contracts:
            if len(contract.state_variables_declared) > 1:
                # since @state_variables_declared is list, it doesn't have .source_mapping of relevant line range
                # so need to build it oursevles from the first and last variable in the list
                lines_str = f"{contract.state_variables_declared[0].source_mapping}-{contract.state_variables_declared[-1].source_mapping.lines[-1]}"
                all_var_collections.append((\
                    f"contract {contract.name} storage variables ({lines_str})",\
                         contract.state_variables_declared))

            for struct in contract.structures:
                 all_var_collections.append((f"struct {struct.canonical_name} ({struct.source_mapping})", \
                    struct.elems_ordered))
        
        for elem_desc, elem_collecetion in all_var_collections:
            if optimized_elem_collecetion := OptimizeVariableOrder.find_optimized_struct_ordering(elem_collecetion):
                info = [f"Optimization opportunity in {elem_desc}:\n"]
                info += ["\toriginal variable order (size: ", \
                    str(OptimizeVariableOrder.find_slots_used(elem_collecetion))," slots)\n"]
                
                for e in elem_collecetion:
                    info += [f"\t\t {e.type} {e.name}\n"]
                info += ["\toptimized variable order (size: ", \
                    str(OptimizeVariableOrder.find_slots_used(optimized_elem_collecetion))," slots)\n"]
                
                for e in optimized_elem_collecetion:
                    info += [f"\t\t {e.type} {e.name}\n"]
                info += ["\n"]

                res = self.generate_result(info)

                results.append(res)
            
        return results
