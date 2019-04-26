import unittest
import subprocess, os, sys

class TestUnusedStateVars(unittest.TestCase):
    testDataFile = "unused_state.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath = testDataDir+testDataFile
    
    def setUp(self):
        outFD = open(self.testFilePath+".out","w")
        errFD = open(self.testFilePath+".err","w")
        p = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','unused-state',self.testFilePath], stdout=outFD,stderr=errFD)
        p.wait()
        outFD.close()
        errFD.close()

    def tearDown(self):
        p = subprocess.Popen(['rm','-f',self.testFilePath+'.out',self.testFilePath+'.err',self.testFilePath+'.format'])
        p.wait()
        
    def test_unused_state_vars(self):
        outFD = open(self.testFilePath+".out","r")
        outFD_lines = outFD.readlines()
        for i in range(len(outFD_lines)):
            outFD_lines[i] = outFD_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD_lines[0].rstrip(),"Number of Slither results: 1")
        self.assertEqual(outFD_lines[1].rstrip(),"Number of patches: 1")
        self.assertEqual(outFD_lines.count("Detector: unused-state"), 1)
        self.assertEqual(outFD_lines.count("Old string: address unused    ;"), 1)
        self.assertEqual(outFD_lines.count("New string:"), 1)
        self.assertEqual(outFD_lines.count("Location start: 44"), 1)
        self.assertEqual(outFD_lines.count("Location end: 63"), 1)
        outFD.close()
    
if __name__ == '__main__':
    unittest.main()
