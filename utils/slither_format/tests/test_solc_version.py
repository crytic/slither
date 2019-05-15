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
        outFD1 = open(self.testFilePath1+".out","r")
        outFD1_lines = outFD1.readlines()
        for i in range(len(outFD1_lines)):
            outFD1_lines[i] = outFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD1_lines[0],"Number of Slither results: 1")
        self.assertEqual(outFD1_lines[1],"Number of patches: 1")
        self.assertEqual(outFD1_lines.count("Detector: solc-version"), 1)
        self.assertEqual(outFD1_lines.count("Old string: pragma solidity ^0.4.23;"), 1)
        self.assertEqual(outFD1_lines.count("New string: pragma solidity 0.4.25;"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 63"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 87"), 1)
        outFD1.close()

        outFD2 = open(self.testFilePath2+".out","r")
        outFD2_lines = outFD2.readlines()
        for i in range(len(outFD2_lines)):
            outFD2_lines[i] = outFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD2_lines[0],"Number of Slither results: 1")
        self.assertEqual(outFD2_lines[1],"Number of patches: 1")
        self.assertEqual(outFD2_lines.count("Detector: solc-version"), 1)
        self.assertEqual(outFD2_lines.count("Old string: pragma solidity >=0.4.0 <0.6.0;"), 1)
        self.assertEqual(outFD2_lines.count("New string: pragma solidity 0.5.3;"), 1)
        self.assertEqual(outFD2_lines.count("Location start: 63"), 1)
        self.assertEqual(outFD2_lines.count("Location end: 94"), 1)
        outFD2.close()

        outFD3 = open(self.testFilePath3+".out","r")
        outFD3_lines = outFD3.readlines()
        for i in range(len(outFD3_lines)):
            outFD3_lines[i] = outFD3_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath3+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD3_lines[0],"Number of Slither results: 1")
        self.assertEqual(outFD3_lines[1],"Number of patches: 1")
        self.assertEqual(outFD3_lines.count("Detector: solc-version"), 1)
        self.assertEqual(outFD3_lines.count("Old string: pragma solidity >=0.4.0 <0.4.25;"), 1)
        self.assertEqual(outFD3_lines.count("New string: pragma solidity 0.4.25;"), 1)
        self.assertEqual(outFD3_lines.count("Location start: 63"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 95"), 1)
        outFD3.close()

        outFD4 = open(self.testFilePath4+".out","r")
        outFD4_lines = outFD4.readlines()
        for i in range(len(outFD4_lines)):
            outFD4_lines[i] = outFD4_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath4+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD4_lines[0],"Number of Slither results: 1")
        self.assertEqual(outFD4_lines[1],"Number of patches: 1")
        self.assertEqual(outFD4_lines.count("Detector: solc-version"), 1)
        self.assertEqual(outFD4_lines.count("Old string: pragma solidity ^0.5.1;"), 1)
        self.assertEqual(outFD4_lines.count("New string: pragma solidity 0.5.3;"), 1)
        self.assertEqual(outFD4_lines.count("Location start: 63"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 86"), 1)
        outFD4.close()

if __name__ == '__main__':
    unittest.main()
