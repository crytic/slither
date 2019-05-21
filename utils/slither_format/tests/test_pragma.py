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
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','pragma',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD1.close()
        errFD1.close()

        outFD2 = open(self.testFilePath2+".out","w")
        errFD2 = open(self.testFilePath2+".err","w")
        my_env = os.environ.copy()
        my_env["SOLC_VERSION"] = "0.5.4"
        p2 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','pragma',self.testFilePath2], stdout=outFD2,stderr=errFD2, env=my_env)
        p2.wait()
        outFD2.close()
        errFD2.close()
        
    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format',self.testImportFilePath1+'.format'])
        p1.wait()

        p2 = subprocess.Popen(['rm','-f',self.testFilePath2+'.out',self.testFilePath2+'.err',self.testFilePath2+'.format',self.testImportFilePath2+'.format'])
        p2.wait()

    def test_pragma(self):
        errFD1 = open(self.testFilePath1+".err","r")
        errFD1_lines = errFD1.readlines()
        for i in range(len(errFD1_lines)):
            errFD1_lines[i] = errFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD1_lines[0],"INFO:Slither.Format:Number of Slither results: 2")
        self.assertEqual(errFD1_lines[1],"INFO:Slither.Format:Number of patches: 2")
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: pragma"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Old string: pragma solidity ^0.4.23;"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Old string: pragma solidity ^0.4.24;"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:New string: pragma solidity 0.4.25;"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location start: 0"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location end: 24"), 2)
        errFD1.close()

        errFD2 = open(self.testFilePath2+".err","r")
        errFD2_lines = errFD2.readlines()
        for i in range(len(errFD2_lines)):
            errFD2_lines[i] = errFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD2_lines[0],"INFO:Slither.Format:Number of Slither results: 2")
        self.assertEqual(errFD2_lines[1],"INFO:Slither.Format:Number of patches: 2")
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Detector: pragma"), 2)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Old string: pragma solidity ^0.5.4;"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Old string: pragma solidity ^0.5.2;"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:New string: pragma solidity 0.5.3;"), 2)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Location start: 0"), 2)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Location end: 23"), 2)
        errFD2.close()

if __name__ == '__main__':
    unittest.main()
