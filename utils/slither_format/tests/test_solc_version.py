import unittest
import subprocess, os, sys
  
class TestSolcVersion(unittest.TestCase):
    testDataDir = "./slither_format/tests/test_data/"
    testDataFile1 = "solc_version_incorrect1.sol"
    testFilePath1 = testDataDir+testDataFile1
    testDataFile2 = "solc_version_incorrect2.sol"
    testFilePath2 = testDataDir+testDataFile2
    testDataFile3 = "solc_version_incorrect3.sol"
    testFilePath3 = testDataDir+testDataFile3
    testDataFile4 = "solc_version_incorrect4.sol"
    testFilePath4 = testDataDir+testDataFile4
    
    def setUp(self):
        outFD1 = open(self.testFilePath1+".out","w")
        errFD1 = open(self.testFilePath1+".err","w")
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','solc-version',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD1.close()
        errFD1.close()

        outFD2 = open(self.testFilePath2+".out","w")
        errFD2 = open(self.testFilePath2+".err","w")
        p2 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','solc-version',self.testFilePath2], stdout=outFD2,stderr=errFD2)
        p2.wait()
        outFD2.close()
        errFD2.close()

        outFD3 = open(self.testFilePath3+".out","w")
        errFD3 = open(self.testFilePath3+".err","w")
        p3 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','solc-version',self.testFilePath3], stdout=outFD3,stderr=errFD3)
        p3.wait()
        outFD3.close()
        errFD3.close()

        outFD4 = open(self.testFilePath4+".out","w")
        errFD4 = open(self.testFilePath4+".err","w")
        my_env = os.environ.copy()
        my_env["SOLC_VERSION"] = "0.5.2"
        p4 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','solc-version',self.testFilePath4], stdout=outFD4,stderr=errFD4, env=my_env)
        p4.wait()
        outFD4.close()
        errFD4.close()

    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format'])
        p1.wait()
        p2 = subprocess.Popen(['rm','-f',self.testFilePath2+'.out',self.testFilePath2+'.err',self.testFilePath2+'.format'])
        p2.wait()
        p3 = subprocess.Popen(['rm','-f',self.testFilePath3+'.out',self.testFilePath3+'.err',self.testFilePath3+'.format'])
        p3.wait()
        p4 = subprocess.Popen(['rm','-f',self.testFilePath4+'.out',self.testFilePath4+'.err',self.testFilePath4+'.format'])
        p4.wait()
        
    def test_solc_version(self):
        errFD1 = open(self.testFilePath1+".err","r")
        errFD1_lines = errFD1.readlines()
        for i in range(len(errFD1_lines)):
            errFD1_lines[i] = errFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD1_lines[0],"INFO:Slither.Format:Number of Slither results: 1")
        self.assertEqual(errFD1_lines[1],"INFO:Slither.Format:Number of patches: 1")
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: solc-version"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Old string: pragma solidity ^0.4.23;"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:New string: pragma solidity 0.4.25;"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location start: 63"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location end: 87"), 1)
        errFD1.close()

        errFD2 = open(self.testFilePath2+".err","r")
        errFD2_lines = errFD2.readlines()
        for i in range(len(errFD2_lines)):
            errFD2_lines[i] = errFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD2_lines[0],"INFO:Slither.Format:Number of Slither results: 1")
        self.assertEqual(errFD2_lines[1],"INFO:Slither.Format:Number of patches: 1")
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Detector: solc-version"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Old string: pragma solidity >=0.4.0 <0.6.0;"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:New string: pragma solidity 0.5.3;"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Location start: 63"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Location end: 94"), 1)
        errFD2.close()

        errFD3 = open(self.testFilePath3+".err","r")
        errFD3_lines = errFD3.readlines()
        for i in range(len(errFD3_lines)):
            errFD3_lines[i] = errFD3_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath3+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD3_lines[0],"INFO:Slither.Format:Number of Slither results: 1")
        self.assertEqual(errFD3_lines[1],"INFO:Slither.Format:Number of patches: 1")
        self.assertEqual(errFD3_lines.count("INFO:Slither.Format:Detector: solc-version"), 1)
        self.assertEqual(errFD3_lines.count("INFO:Slither.Format:Old string: pragma solidity >=0.4.0 <0.4.25;"), 1)
        self.assertEqual(errFD3_lines.count("INFO:Slither.Format:New string: pragma solidity 0.4.25;"), 1)
        self.assertEqual(errFD3_lines.count("INFO:Slither.Format:Location start: 63"), 1)
        self.assertEqual(errFD3_lines.count("INFO:Slither.Format:Location end: 95"), 1)
        errFD3.close()

        errFD4 = open(self.testFilePath4+".err","r")
        errFD4_lines = errFD4.readlines()
        for i in range(len(errFD4_lines)):
            errFD4_lines[i] = errFD4_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath4+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD4_lines[0],"INFO:Slither.Format:Number of Slither results: 1")
        self.assertEqual(errFD4_lines[1],"INFO:Slither.Format:Number of patches: 1")
        self.assertEqual(errFD4_lines.count("INFO:Slither.Format:Detector: solc-version"), 1)
        self.assertEqual(errFD4_lines.count("INFO:Slither.Format:Old string: pragma solidity ^0.5.1;"), 1)
        self.assertEqual(errFD4_lines.count("INFO:Slither.Format:New string: pragma solidity 0.5.3;"), 1)
        self.assertEqual(errFD4_lines.count("INFO:Slither.Format:Location start: 63"), 1)
        self.assertEqual(errFD4_lines.count("INFO:Slither.Format:Location end: 86"), 1)
        errFD4.close()

if __name__ == '__main__':
    unittest.main()
