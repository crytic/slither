import unittest
import subprocess, os, sys
  
class TestExternalFunctions(unittest.TestCase):
    testDataFile = "external_function.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath = testDataDir+testDataFile
    
    def setUp(self):
        outFD = open(self.testFilePath+".out","w")
        errFD = open(self.testFilePath+".err","w")
        p = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','external-function',self.testFilePath], stdout=outFD,stderr=errFD)
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
        self.assertEqual(outFD_lines[0],"Number of patches: 6")
        self.assertEqual(outFD_lines.count("Detector: external-function"), 6)
        self.assertEqual(outFD_lines.count("Old string: (uint _i)    public returns"), 1)
        self.assertEqual(outFD_lines.count("New string: (uint _i)    external returns"), 1)
        self.assertEqual(outFD_lines.count("Location start: 311"), 1)
        self.assertEqual(outFD_lines.count("Location end: 342"), 1)
        self.assertEqual(outFD_lines.count("Old string: ()"), 1)
        self.assertEqual(outFD_lines.count("New string: () extern"), 1)
        self.assertEqual(outFD_lines.count("Location start: 463"), 1)
        self.assertEqual(outFD_lines.count("Location end: 473"), 1)
        self.assertEqual(outFD_lines.count("Old string: () public    returns"), 1)
        self.assertEqual(outFD_lines.count("New string: () external    returns"), 1)
        self.assertEqual(outFD_lines.count("Location start: 500"), 1)
        self.assertEqual(outFD_lines.count("Location end: 524"), 1)
        self.assertEqual(outFD_lines.count("Old string: () public"), 3)
        self.assertEqual(outFD_lines.count("New string: () external"), 3)
        self.assertEqual(outFD_lines.count("Location start: 580"), 1)
        self.assertEqual(outFD_lines.count("Location end: 592"), 1)
        self.assertEqual(outFD_lines.count("Location start: 623"), 1)
        self.assertEqual(outFD_lines.count("Location end: 635"), 1)
        self.assertEqual(outFD_lines.count("Location start: 818"), 1)
        self.assertEqual(outFD_lines.count("Location end: 830"), 1)
        outFD.close()
    
if __name__ == '__main__':
    unittest.main()
