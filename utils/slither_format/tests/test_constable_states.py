import unittest
import subprocess, os, sys

class TestConstableState(unittest.TestCase):
    testDataFile = "const_state_variables.sol"
    testDataDir = "./slither_format/tests/test_data/"
    testFilePath = testDataDir+testDataFile
    
    def setUp(self):
        outFD = open(self.testFilePath+".out","w")
        errFD = open(self.testFilePath+".err","w")
        p = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','constable-states',self.testFilePath], stdout=outFD,stderr=errFD)
        p.wait()
        outFD.close()
        errFD.close()

    def tearDown(self):
        p = subprocess.Popen(['rm','-f',self.testFilePath+'.out',self.testFilePath+'.err',self.testFilePath+'.format'])
        p.wait()
        
    def test_constable_states(self):
        outFD = open(self.testFilePath+".out","r")
        outFD_lines = outFD.readlines()
        for i in range(len(outFD_lines)):
            outFD_lines[i] = outFD_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD_lines[0].rstrip(),"Number of Slither results: 6")
        self.assertEqual(outFD_lines[1].rstrip(),"Number of patches: 6")
        self.assertEqual(outFD_lines.count("Detector: constable-states"), 6)
        self.assertEqual(outFD_lines.count("Old string: address public myFriendsAddress = 0xc0ffee254729296a45a3885639AC7E10F9d54979"), 1)
        self.assertEqual(outFD_lines.count("New string: address public constant myFriendsAddress = 0xc0ffee254729296a45a3885639AC7E10F9d54979"), 1)
        self.assertEqual(outFD_lines.count("Location start: 132"), 1)
        self.assertEqual(outFD_lines.count("Location end: 208"), 1)
        self.assertEqual(outFD_lines.count("Old string: uint public test = 5"), 1)
        self.assertEqual(outFD_lines.count("New string: uint public constant test = 5"), 1)
        self.assertEqual(outFD_lines.count("Location start: 237"), 1)
        self.assertEqual(outFD_lines.count("Location end: 257"), 1)
        self.assertEqual(outFD_lines.count("Old string: string text2 = \"xyz\""), 1)
        self.assertEqual(outFD_lines.count("New string: string constant text2 = \"xyz\""), 1)
        self.assertEqual(outFD_lines.count("Location start: 333"), 1)
        self.assertEqual(outFD_lines.count("Location end: 353"), 1)
        self.assertEqual(outFD_lines.count("Old string: address public mySistersAddress = 0x999999cf1046e68e36E1aA2E0E07105eDDD1f08E"), 1)
        self.assertEqual(outFD_lines.count("New string: address public constant mySistersAddress = 0x999999cf1046e68e36E1aA2E0E07105eDDD1f08E"), 1)
        self.assertEqual(outFD_lines.count("Location start: 496"), 1)
        self.assertEqual(outFD_lines.count("Location end: 572"), 1)
        self.assertEqual(outFD_lines.count("Old string: bytes32 should_be_constant = sha256('abc')"), 1)
        self.assertEqual(outFD_lines.count("New string: bytes32 constant should_be_constant = sha256('abc')"), 1)
        self.assertEqual(outFD_lines.count("Location start: 793"), 1)
        self.assertEqual(outFD_lines.count("Location end: 835"), 1)
        self.assertEqual(outFD_lines.count("Old string: uint should_be_constant_2 = A + 1"), 1)
        self.assertEqual(outFD_lines.count("New string: uint constant should_be_constant_2 = A + 1"), 1)
        self.assertEqual(outFD_lines.count("Location start: 841"), 1)
        self.assertEqual(outFD_lines.count("Location end: 874"), 1)
        outFD.close()
    
if __name__ == '__main__':
    unittest.main()
