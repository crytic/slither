import unittest
import subprocess, os, sys
  
class TestNamingConvention(unittest.TestCase):
    testDataFile1 = "naming_convention_contract.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath1 = testDataDir+testDataFile1
    
    def setUp(self):
        outFD1 = open(self.testFilePath1+".out","w")
        errFD1 = open(self.testFilePath1+".err","w")
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD1.close()
        errFD1.close()
        
    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format'])
        p1.wait()
        
    def test_naming_convention_contract(self):
        outFD1 = open(self.testFilePath1+".out","r")
        outFD1_lines = outFD1.readlines()
        outFD1.close()
        for i in range(len(outFD1_lines)):
            outFD1_lines[i] = outFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD1_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD1_lines[1],"Number of patches: 9")
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract definition)"), 2)
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract state variable)"), 2)
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract function variable)"), 5)
        self.assertEqual(outFD1_lines.count("Old string: contract one"), 1)
        self.assertEqual(outFD1_lines.count("New string: contract One"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 53"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 65"), 1)
        self.assertEqual(outFD1_lines.count("Old string: three k"), 1)
        self.assertEqual(outFD1_lines.count("New string: Three k"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 117"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 124"), 1)
        self.assertEqual(outFD1_lines.count("Old string: three l"), 1)
        self.assertEqual(outFD1_lines.count("New string: Three l"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 206"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 213"), 1)
        self.assertEqual(outFD1_lines.count("Old string: one m"), 1)
        self.assertEqual(outFD1_lines.count("New string: One m"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 343"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 348"), 1)
        self.assertEqual(outFD1_lines.count("Old string: one n"), 1)
        self.assertEqual(outFD1_lines.count("New string: One n"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 423"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 428"), 1)
        self.assertEqual(outFD1_lines.count("Old string: contract three"), 1)
        self.assertEqual(outFD1_lines.count("New string: contract Three"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 498"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 512"), 1)
        self.assertEqual(outFD1_lines.count("Old string: one"), 1)
        self.assertEqual(outFD1_lines.count("New string: One"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 646"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 649"), 1)
        self.assertEqual(outFD1_lines.count("Old string: one r = new one()"), 1)
        self.assertEqual(outFD1_lines.count("New string: One r = new one()"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 773"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 790"), 1)
        self.assertEqual(outFD1_lines.count("Old string: one q"), 1)
        self.assertEqual(outFD1_lines.count("New string: One q"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 871"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 876"), 1)
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract new object)"), 1)
        self.assertEqual(outFD1_lines.count("Old string: one r = new one()"), 2)
        self.assertEqual(outFD1_lines.count("New string: One r = new one()"), 2)
        self.assertEqual(outFD1_lines.count("Location start: 773"), 2)
        self.assertEqual(outFD1_lines.count("Location end: 790"), 2)
    
if __name__ == '__main__':
    unittest.main()
