import unittest
import subprocess, os, sys
  
class TestConstantFunctions(unittest.TestCase):
    testDataFile1 = "constant.sol"
    testDataFile2 = "constant-0.5.1.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath1 = testDataDir+testDataFile1
    testFilePath2 = testDataDir+testDataFile2
    
    def setUp(self):
        outFD1 = open(self.testFilePath1+".out","w")
        errFD1 = open(self.testFilePath1+".err","w")
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','constant-function',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD2 = open(self.testFilePath2+".out","w")
        errFD2 = open(self.testFilePath2+".err","w")
        p2 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','constant-function',self.testFilePath2], stdout=outFD2,stderr=errFD2)
        p2.wait()
        outFD1.close()
        errFD1.close()
        outFD2.close()
        errFD2.close()
        
    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format'])
        p1.wait()
        p2 = subprocess.Popen(['rm','-f',self.testFilePath2+'.out',self.testFilePath2+'.err',self.testFilePath2+'.format'])
        p2.wait()
        
    def test_constant_function(self):
        errFD1 = open(self.testFilePath1+".err","r")
        errFD1_lines = errFD1.readlines()
        for i in range(len(errFD1_lines)):
            errFD1_lines[i] = errFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD1_lines[0],"INFO:Slither.Format:Number of Slither results: 3")
        self.assertEqual(errFD1_lines[1],"INFO:Slither.Format:Number of patches: 3")
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: constant-function"), 3)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Old string: view"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Old string: constant"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:New string:"), 3)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location start: 77"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location end: 81"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location start: 149"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location end: 157"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location start: 360"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Location end: 364"), 1)
        errFD1.close()
        
        errFD2 = open(self.testFilePath2+".err","r")
        errFD2_lines = errFD2.readlines()
        for i in range(len(errFD2_lines)):
            errFD2_lines[i] = errFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD2_lines[0],"INFO:Slither.Format:Number of Slither results: 1")
        self.assertEqual(errFD2_lines[1],"INFO:Slither.Format:Number of patches: 1")
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Old string: view"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:New string:"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Location start: 221"), 1)
        self.assertEqual(errFD2_lines.count("INFO:Slither.Format:Location end: 225"), 1)
        errFD2.close()
        
if __name__ == '__main__':
    unittest.main()
