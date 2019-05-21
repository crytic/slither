import unittest
import subprocess, os, sys
  
class TestDetectorCombinations(unittest.TestCase):
    testDataDir = "./slither_format/tests/test_data/"
    testDataFile1 = "detector_combinations.sol"
    testFilePath1 = testDataDir+testDataFile1

    def setUp(self):
        outFD1 = open(self.testFilePath1+".out","w")
        errFD1 = open(self.testFilePath1+".err","w")
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD1.close()
        errFD1.close()

    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format'])
        p1.wait()
        
    def test_detector_combinations(self):
        errFD1 = open(self.testFilePath1+".err","r")
        errFD1_lines = errFD1.readlines()
        errFD1.close()
        for i in range(len(errFD1_lines)):
            errFD1_lines[i] = errFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Number of Slither results: 12"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Number of patches: 19"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Overlapping patch won't be applied!"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:xDetector: unused-state"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:xDetector: constable-states"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: naming-convention (state variable declaration)"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: naming-convention (state variable uses)"), 3)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: naming-convention (parameter declaration)"), 4)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: naming-convention (parameter uses)"), 6)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: external-function"), 2)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: constant-function"), 1)
        self.assertEqual(errFD1_lines.count("INFO:Slither.Format:Detector: solc-version"), 1)
if __name__ == '__main__':
    unittest.main()
