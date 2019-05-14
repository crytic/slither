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
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','constant-function',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD2 = open(self.testFilePath2+".out","w")
        errFD2 = open(self.testFilePath2+".err","w")
        p2 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','constant-function',self.testFilePath2], stdout=outFD2,stderr=errFD2)
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
        outFD1 = open(self.testFilePath1+".out","r")
        outFD1_lines = outFD1.readlines()
        for i in range(len(outFD1_lines)):
            outFD1_lines[i] = outFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD1_lines[0],"Number of Slither results: 3")
        self.assertEqual(outFD1_lines[1],"Number of patches: 3")
        self.assertEqual(outFD1_lines.count("Detector: constant-function"), 3)
        self.assertEqual(outFD1_lines.count("Old string: view"), 2)
        self.assertEqual(outFD1_lines.count("Old string: constant"), 1)
        self.assertEqual(outFD1_lines.count("New string:"), 3)
        self.assertEqual(outFD1_lines.count("Location start: 77"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 81"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 149"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 157"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 360"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 364"), 1)
        outFD1.close()
        
        outFD2 = open(self.testFilePath2+".out","r")
        outFD2_lines = outFD2.readlines()
        for i in range(len(outFD2_lines)):
            outFD2_lines[i] = outFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD2_lines[0],"Number of Slither results: 1")
        self.assertEqual(outFD2_lines[1],"Number of patches: 1")
        self.assertEqual(outFD2_lines.count("Old string: view"), 1)
        self.assertEqual(outFD2_lines.count("New string:"), 1)
        self.assertEqual(outFD2_lines.count("Location start: 221"), 1)
        self.assertEqual(outFD2_lines.count("Location end: 225"), 1)
        outFD2.close()
        
if __name__ == '__main__':
    unittest.main()
