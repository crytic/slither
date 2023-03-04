from slither import Slither
from slither import InefficientInequalityDetector

slither = Slither('')
detector = InefficientInequalityDetector(slither.contracts)
detector.analyze()
results = detector.get_results()
for contract_name in results:
    print(f"Results for {contract_name}:")
    for result in results[contract_name]:
        print(f"\t{result.description}")
