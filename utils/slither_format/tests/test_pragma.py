import unittest
import subprocess, os, sys
  
class TestPragma(unittest.TestCase):
    testDataDir = "./slither_format/tests/test_data/"
    testDataFile1 = "pragma.0.4.24.sol"
    testImportFile1 = "pragma.0.4.23.sol"
    testFilePath1 = testDataDir+testDataFile1
    testImportFilePath1 = testDataDir+testImportFile1
    testDataFile2 = "pragma.0.5.4.sol"
    testImportFile2 = "pragma.0.5.2.sol"
    testFilePath2 = testDataDir+testDataFile2
    testImportFilePath2 = testDataDir+testImportFile2
    
    def setUp(self):
        outFD1 = open(self.testFilePath1+".out","w")
        errFD1 = open(self.testFilePath1+".err","w")
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','pragma',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD1.close()
        errFD1.close()

        outFD2 = open(self.testFilePath2+".out","w")
        errFD2 = open(self.testFilePath2+".err","w")
        my_env = os.environ.copy()
        my_env["SOLC_VERSION"] = "0.5.4"
        p2 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','pragma',self.testFilePath2], stdout=outFD2,stderr=errFD2, env=my_env)
        p2.wait()
        outFD2.close()
        errFD2.close()
        
    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format',self.testImportFilePath1+'.format'])
        p1.wait()

        p2 = subprocess.Popen(['rm','-f',self.testFilePath2+'.out',self.testFilePath2+'.err',self.testFilePath2+'.format',self.testImportFilePath2+'.format'])
        p2.wait()

    def test_pragma(self):
        outFD1 = open(self.testFilePath1+".out","r")
        outFD1_lines = outFD1.readlines()
        for i in range(len(outFD1_lines)):
            outFD1_lines[i] = outFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD1_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD1_lines[1],"Number of patches: 2")
        self.assertEqual(outFD1_lines.count("Detector: pragma"), 2)
        self.assertEqual(outFD1_lines.count("Old string: pragma solidity ^0.4.23;"), 1)
        self.assertEqual(outFD1_lines.count("Old string: pragma solidity ^0.4.24;"), 1)
        self.assertEqual(outFD1_lines.count("New string: pragma solidity 0.4.25;"), 2)
        self.assertEqual(outFD1_lines.count("Location start: 0"), 2)
        self.assertEqual(outFD1_lines.count("Location end: 24"), 2)
        outFD1.close()

        outFD2 = open(self.testFilePath2+".out","r")
        outFD2_lines = outFD2.readlines()
        for i in range(len(outFD2_lines)):
            outFD2_lines[i] = outFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD2_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD2_lines[1],"Number of patches: 2")
        self.assertEqual(outFD2_lines.count("Detector: pragma"), 2)
        self.assertEqual(outFD2_lines.count("Old string: pragma solidity ^0.5.4;"), 1)
        self.assertEqual(outFD2_lines.count("Old string: pragma solidity ^0.5.2;"), 1)
        self.assertEqual(outFD2_lines.count("New string: pragma solidity 0.5.3;"), 2)
        self.assertEqual(outFD2_lines.count("Location start: 0"), 2)
        self.assertEqual(outFD2_lines.count("Location end: 23"), 2)
        outFD2.close()

if __name__ == '__main__':
    unittest.main()
