import unittest
import subprocess, os, sys

class TestUnusedStateVars(unittest.TestCase):
    testDataFile = "unused_state.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath = testDataDir+testDataFile
    
    def setUp(self):
        outFD = open(self.testFilePath+".out","w")
        errFD = open(self.testFilePath+".err","w")
        p = subprocess.Popen(['python3', '-m', 'slither_format','--verbose-test','--detect','unused-state',self.testFilePath], stdout=outFD,stderr=errFD)
        p.wait()
        outFD.close()
        errFD.close()

    def tearDown(self):
        p = subprocess.Popen(['rm','-f',self.testFilePath+'.out',self.testFilePath+'.err',self.testFilePath+'.format'])
        p.wait()
        
    def test_unused_state_vars(self):
        errFD = open(self.testFilePath+".err","r")
        errFD_lines = errFD.readlines()
        for i in range(len(errFD_lines)):
            errFD_lines[i] = errFD_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath+".format"),"Patched .format file is not created?!")
        self.assertEqual(errFD_lines[0].rstrip(),"INFO:Slither.Format:Number of Slither results: 1")
        self.assertEqual(errFD_lines[1].rstrip(),"INFO:Slither.Format:Number of patches: 1")
        self.assertEqual(errFD_lines.count("INFO:Slither.Format:Detector: unused-state"), 1)
        self.assertEqual(errFD_lines.count("INFO:Slither.Format:Old string: address unused    ;"), 1)
        self.assertEqual(errFD_lines.count("INFO:Slither.Format:New string:"), 1)
        self.assertEqual(errFD_lines.count("INFO:Slither.Format:Location start: 44"), 1)
        self.assertEqual(errFD_lines.count("INFO:Slither.Format:Location end: 63"), 1)
        errFD.close()
    
if __name__ == '__main__':
    unittest.main()
