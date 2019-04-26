import unittest
import subprocess, os, sys
  
class TestSolcVersion(unittest.TestCase):
    testDataFile = "solc_version_incorrect.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath = testDataDir+testDataFile
    
    def setUp(self):
        outFD = open(self.testFilePath+".out","w")
        errFD = open(self.testFilePath+".err","w")
        p = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','solc-version',self.testFilePath], stdout=outFD,stderr=errFD)
        p.wait()
        outFD.close()
        errFD.close()
        
    def tearDown(self):
        p = subprocess.Popen(['rm','-f',self.testFilePath+'.out',self.testFilePath+'.err',self.testFilePath+'.format'])
        p.wait()
        
    def test_solc_version(self):
        outFD = open(self.testFilePath+".out","r")
        outFD_lines = outFD.readlines()
        for i in range(len(outFD_lines)):
            outFD_lines[i] = outFD_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD_lines[1],"Number of patches: 2")
        self.assertEqual(outFD_lines.count("Detector: solc-version"), 2)
        self.assertEqual(outFD_lines.count("Old string: pragma solidity ^0.4.23;"), 1)
        self.assertEqual(outFD_lines.count("Old string: pragma solidity >=0.4.0 <0.6.0;"), 1)
        self.assertEqual(outFD_lines.count("New string: pragma solidity ^0.4.25;"), 2)
        self.assertEqual(outFD_lines.count("Location start: 63"), 1)
        self.assertEqual(outFD_lines.count("Location end: 87"), 1)
        self.assertEqual(outFD_lines.count("Location start: 89"), 1)
        self.assertEqual(outFD_lines.count("Location end: 120"), 1)
        self.assertEqual(outFD_lines.count("Patch file: ./slither_format/tests/test_data/solc_version_incorrect.sol"), 1)
        outFD.close()

if __name__ == '__main__':
    unittest.main()
