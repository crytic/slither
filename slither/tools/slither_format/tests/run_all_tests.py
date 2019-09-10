import subprocess

p9 = subprocess.Popen(['python3', './slither_format/tests/test_unicode.py'])
p9.wait()
p8 = subprocess.Popen(['python3', './slither_format/tests/test_detector_combinations.py'])
p8.wait()
p7 = subprocess.Popen(['python3', './slither_format/tests/test_solc_version.py'])
p7.wait()
p6 = subprocess.Popen(['python3', './slither_format/tests/test_pragma.py'])
p6.wait()
p5 = subprocess.Popen(['python3', './slither_format/tests/test_naming_convention.py'])
p5.wait()
p4 = subprocess.Popen(['python3', './slither_format/tests/test_unused_state_vars.py'])
p4.wait()
p3 = subprocess.Popen(['python3', './slither_format/tests/test_external_function.py'])
p3.wait()
p2 = subprocess.Popen(['python3', './slither_format/tests/test_constant_function.py'])
p2.wait()
p1 = subprocess.Popen(['python3', './slither_format/tests/test_constable_states.py'])
p1.wait()


