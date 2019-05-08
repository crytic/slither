import unittest
import subprocess, os, sys
  
class TestNamingConvention(unittest.TestCase):
    testDataDir = "./slither_format/tests/test_data/"
    testDataFile1 = "naming_convention_contract.sol"
    testDataFile2 = "naming_convention_modifier.sol"
    testDataFile3 = "naming_convention_structure.sol"
    testDataFile4 = "naming_convention_enum.sol"
    testDataFile5 = "naming_convention_event.sol"
    testDataFile6 = "naming_convention_function.sol"
    testDataFile7 = "naming_convention_parameter.sol"
    testDataFile8 = "naming_convention_state_variable.sol"
    testFilePath1 = testDataDir+testDataFile1
    testFilePath2 = testDataDir+testDataFile2
    testFilePath3 = testDataDir+testDataFile3
    testFilePath4 = testDataDir+testDataFile4
    testFilePath5 = testDataDir+testDataFile5
    testFilePath6 = testDataDir+testDataFile6
    testFilePath7 = testDataDir+testDataFile7
    testFilePath8 = testDataDir+testDataFile8
    
    def setUp(self):
        outFD1 = open(self.testFilePath1+".out","w")
        errFD1 = open(self.testFilePath1+".err","w")
        p1 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath1], stdout=outFD1,stderr=errFD1)
        p1.wait()
        outFD1.close()
        errFD1.close()

        outFD2 = open(self.testFilePath2+".out","w")
        errFD2 = open(self.testFilePath2+".err","w")
        p2 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath2], stdout=outFD2,stderr=errFD2)
        p2.wait()
        outFD2.close()
        errFD2.close()

        outFD3 = open(self.testFilePath3+".out","w")
        errFD3 = open(self.testFilePath3+".err","w")
        p3 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath3], stdout=outFD3,stderr=errFD3)
        p3.wait()
        outFD3.close()
        errFD3.close()

        outFD4 = open(self.testFilePath4+".out","w")
        errFD4 = open(self.testFilePath4+".err","w")
        p4 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath4], stdout=outFD4,stderr=errFD4)
        p4.wait()
        outFD4.close()
        errFD4.close()

        outFD5 = open(self.testFilePath5+".out","w")
        errFD5 = open(self.testFilePath5+".err","w")
        p5 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath5], stdout=outFD5,stderr=errFD5)
        p5.wait()
        outFD5.close()
        errFD5.close()

        outFD6 = open(self.testFilePath6+".out","w")
        errFD6 = open(self.testFilePath6+".err","w")
        p6 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath6], stdout=outFD6,stderr=errFD6)
        p6.wait()
        outFD6.close()
        errFD6.close()

        outFD7 = open(self.testFilePath7+".out","w")
        errFD7 = open(self.testFilePath7+".err","w")
        p7 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath7], stdout=outFD7,stderr=errFD7)
        p7.wait()
        outFD7.close()
        errFD7.close()

        outFD8 = open(self.testFilePath8+".out","w")
        errFD8 = open(self.testFilePath8+".err","w")
        p8 = subprocess.Popen(['python3', '-m', 'slither_format','--verbose','--detect','naming-convention',self.testFilePath8], stdout=outFD8,stderr=errFD8)
        p8.wait()
        outFD8.close()
        errFD8.close()

    def tearDown(self):
        p1 = subprocess.Popen(['rm','-f',self.testFilePath1+'.out',self.testFilePath1+'.err',self.testFilePath1+'.format'])
        p1.wait()
        p2 = subprocess.Popen(['rm','-f',self.testFilePath2+'.out',self.testFilePath2+'.err',self.testFilePath2+'.format'])
        p2.wait()
        p3 = subprocess.Popen(['rm','-f',self.testFilePath3+'.out',self.testFilePath3+'.err',self.testFilePath3+'.format'])
        p3.wait()
        p4 = subprocess.Popen(['rm','-f',self.testFilePath4+'.out',self.testFilePath4+'.err',self.testFilePath4+'.format'])
        p4.wait()
        p5 = subprocess.Popen(['rm','-f',self.testFilePath5+'.out',self.testFilePath5+'.err',self.testFilePath5+'.format'])
        p5.wait()
        p6 = subprocess.Popen(['rm','-f',self.testFilePath6+'.out',self.testFilePath6+'.err',self.testFilePath6+'.format'])
        p6.wait()
        p7 = subprocess.Popen(['rm','-f',self.testFilePath7+'.out',self.testFilePath7+'.err',self.testFilePath7+'.format'])
        p7.wait()
        p8 = subprocess.Popen(['rm','-f',self.testFilePath8+'.out',self.testFilePath8+'.err',self.testFilePath8+'.format'])
        p8.wait()
        
    def test_naming_convention_contract(self):
        outFD1 = open(self.testFilePath1+".out","r")
        outFD1_lines = outFD1.readlines()
        outFD1.close()
        for i in range(len(outFD1_lines)):
            outFD1_lines[i] = outFD1_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath1+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD1_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD1_lines[1],"Number of patches: 10")
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract definition)"), 2)
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract state variable)"), 2)
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract function variable)"), 5)
        self.assertEqual(outFD1_lines.count("Detector: naming-convention (contract new object)"), 1)
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
        self.assertEqual(outFD1_lines.count("Old string: new one()"), 1)
        self.assertEqual(outFD1_lines.count("New string: new One()"), 1)
        self.assertEqual(outFD1_lines.count("Location start: 781"), 1)
        self.assertEqual(outFD1_lines.count("Location end: 788"), 1)

    def test_naming_convention_modifier(self):
        outFD2 = open(self.testFilePath2+".out","r")
        outFD2_lines = outFD2.readlines()
        outFD2.close()
        for i in range(len(outFD2_lines)):
            outFD2_lines[i] = outFD2_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath2+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD2_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD2_lines[1],"Number of patches: 4")
        self.assertEqual(outFD2_lines.count("Detector: naming-convention (modifier definition)"), 2)
        self.assertEqual(outFD2_lines.count("Detector: naming-convention (modifier uses)"), 2)
        self.assertEqual(outFD2_lines.count("Old string: modifier One"), 1)
        self.assertEqual(outFD2_lines.count("New string: modifier one"), 1)
        self.assertEqual(outFD2_lines.count("Location start: 215"), 1)
        self.assertEqual(outFD2_lines.count("Location end: 227"), 1)
        self.assertEqual(outFD2_lines.count("Old string: () One"), 1)
        self.assertEqual(outFD2_lines.count("New string: () one"), 1)
        self.assertEqual(outFD2_lines.count("Location start: 288"), 1)
        self.assertEqual(outFD2_lines.count("Location end: 295"), 1)
        self.assertEqual(outFD2_lines.count("Old string: modifier Two"), 1)
        self.assertEqual(outFD2_lines.count("New string: modifier two"), 1)
        self.assertEqual(outFD2_lines.count("Location start: 423"), 1)
        self.assertEqual(outFD2_lines.count("Location end: 435"), 1)
        self.assertEqual(outFD2_lines.count("Old string: () one Two returns"), 1)
        self.assertEqual(outFD2_lines.count("New string: () one two returns"), 1)
        self.assertEqual(outFD2_lines.count("Location start: 503"), 1)
        self.assertEqual(outFD2_lines.count("Location end: 522"), 1)

    def test_naming_convention_structure(self):
        outFD3 = open(self.testFilePath3+".out","r")
        outFD3_lines = outFD3.readlines()
        outFD3.close()
        for i in range(len(outFD3_lines)):
            outFD3_lines[i] = outFD3_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath3+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD3_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD3_lines[1],"Number of patches: 6")
        self.assertEqual(outFD3_lines.count("Detector: naming-convention (struct definition)"), 2)
        self.assertEqual(outFD3_lines.count("Detector: naming-convention (struct use)"), 4)
        self.assertEqual(outFD3_lines.count("Old string: struct s {    uint i;  }"), 2)
        self.assertEqual(outFD3_lines.count("New string: struct S {    uint i;  }"), 2)
        self.assertEqual(outFD3_lines.count("Location start: 108"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 134"), 1)
        self.assertEqual(outFD3_lines.count("Location start: 434"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 460"), 1)
        self.assertEqual(outFD3_lines.count("Old string: s s1"), 2)
        self.assertEqual(outFD3_lines.count("New string: S s1"), 2)
        self.assertEqual(outFD3_lines.count("Location start: 171"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 175"), 1)
        self.assertEqual(outFD3_lines.count("Location start: 497"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 501"), 1)
        self.assertEqual(outFD3_lines.count("Old string: s sA"), 1)
        self.assertEqual(outFD3_lines.count("New string: S sA"), 1)
        self.assertEqual(outFD3_lines.count("Location start: 570"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 574"), 1)
        self.assertEqual(outFD3_lines.count("Old string: s"), 1)
        self.assertEqual(outFD3_lines.count("New string: S"), 1)
        self.assertEqual(outFD3_lines.count("Location start: 585"), 1)
        self.assertEqual(outFD3_lines.count("Location end: 586"), 1)

    def test_naming_convention_enum(self):
        outFD4 = open(self.testFilePath4+".out","r")
        outFD4_lines = outFD4.readlines()
        outFD4.close()
        for i in range(len(outFD4_lines)):
            outFD4_lines[i] = outFD4_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath4+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD4_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD4_lines[1],"Number of patches: 8")
        self.assertEqual(outFD4_lines.count("Detector: naming-convention (enum definition)"), 2)
        self.assertEqual(outFD4_lines.count("Detector: naming-convention (enum use)"), 6)
        self.assertEqual(outFD4_lines.count("Old string: enum e {ONE, TWO}"), 2)
        self.assertEqual(outFD4_lines.count("New string: enum E {ONE, TWO}"), 2)
        self.assertEqual(outFD4_lines.count("Location start: 73"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 90"), 1)
        self.assertEqual(outFD4_lines.count("Location start: 426"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 443"), 1)
        self.assertEqual(outFD4_lines.count("Old string: e e1"), 2)
        self.assertEqual(outFD4_lines.count("New string: E e1"), 2)
        self.assertEqual(outFD4_lines.count("Location start: 125"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 129"), 1)
        self.assertEqual(outFD4_lines.count("Location start: 478"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 482"), 1)
        self.assertEqual(outFD4_lines.count("Old string: e eA"), 1)
        self.assertEqual(outFD4_lines.count("New string: E eA"), 1)
        self.assertEqual(outFD4_lines.count("Location start: 549"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 553"), 1)
        self.assertEqual(outFD4_lines.count("Old string: e e2 = eA"), 1)
        self.assertEqual(outFD4_lines.count("New string: E e2 = eA"), 1)
        self.assertEqual(outFD4_lines.count("Location start: 573"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 582"), 1)
        self.assertEqual(outFD4_lines.count("Old string:  e.ONE"), 1)
        self.assertEqual(outFD4_lines.count("New string:  E.ONE"), 1)
        self.assertEqual(outFD4_lines.count("Location start: 186"), 1)
        self.assertEqual(outFD4_lines.count("Location end: 192"), 1)
        
    def test_naming_convention_event(self):
        outFD5 = open(self.testFilePath5+".out","r")
        outFD5_lines = outFD5.readlines()
        outFD5.close()
        for i in range(len(outFD5_lines)):
            outFD5_lines[i] = outFD5_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath5+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD5_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD5_lines[1],"Number of patches: 4")
        self.assertEqual(outFD5_lines.count("Detector: naming-convention (event definition)"), 2)
        self.assertEqual(outFD5_lines.count("Detector: naming-convention (event calls)"), 2)
        self.assertEqual(outFD5_lines.count("Old string: event e(uint);"), 2)
        self.assertEqual(outFD5_lines.count("New string: event E(uint);"), 2)
        self.assertEqual(outFD5_lines.count("Location start: 75"), 1)
        self.assertEqual(outFD5_lines.count("Location end: 89"), 1)
        self.assertEqual(outFD5_lines.count("Location start: 148"), 1)
        self.assertEqual(outFD5_lines.count("Location end: 152"), 1)
        self.assertEqual(outFD5_lines.count("Old string: e(i)"), 2)
        self.assertEqual(outFD5_lines.count("New string: E(i)"), 2)
        self.assertEqual(outFD5_lines.count("Location start: 148"), 1)
        self.assertEqual(outFD5_lines.count("Location end: 152"), 1)
        self.assertEqual(outFD5_lines.count("Location start: 438"), 1)
        self.assertEqual(outFD5_lines.count("Location end: 442"), 1)

    def test_naming_convention_function(self):
        outFD6 = open(self.testFilePath6+".out","r")
        outFD6_lines = outFD6.readlines()
        outFD6.close()
        for i in range(len(outFD6_lines)):
            outFD6_lines[i] = outFD6_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath6+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD6_lines[0],"Number of Slither results: 2")
        self.assertEqual(outFD6_lines[1],"Number of patches: 4")
        self.assertEqual(outFD6_lines.count("Detector: naming-convention (function definition)"), 2)
        self.assertEqual(outFD6_lines.count("Detector: naming-convention (function calls)"), 2)
        self.assertEqual(outFD6_lines.count("Old string: function Foo"), 1)
        self.assertEqual(outFD6_lines.count("New string: function foo"), 1)
        self.assertEqual(outFD6_lines.count("Location start: 76"), 1)
        self.assertEqual(outFD6_lines.count("Location end: 88"), 1)
        self.assertEqual(outFD6_lines.count("Old string: function Foobar"), 1)
        self.assertEqual(outFD6_lines.count("New string: function foobar"), 1)
        self.assertEqual(outFD6_lines.count("Location start: 189"), 1)
        self.assertEqual(outFD6_lines.count("Location end: 204"), 1)
        self.assertEqual(outFD6_lines.count("Old string: Foobar(10)"), 1)
        self.assertEqual(outFD6_lines.count("New string: foobar(10)"), 1)
        self.assertEqual(outFD6_lines.count("Location start: 136"), 1)
        self.assertEqual(outFD6_lines.count("Location end: 146"), 1)
        self.assertEqual(outFD6_lines.count("Old string: a.Foobar(10)"), 1)
        self.assertEqual(outFD6_lines.count("New string: a.foobar(10)"), 1)
        self.assertEqual(outFD6_lines.count("Location start: 516"), 1)
        self.assertEqual(outFD6_lines.count("Location end: 528"), 1)

    def test_naming_convention_parameter(self):
        outFD7 = open(self.testFilePath7+".out","r")
        outFD7_lines = outFD7.readlines()
        outFD7.close()
        for i in range(len(outFD7_lines)):
            outFD7_lines[i] = outFD7_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath7+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD7_lines[0],"Number of Slither results: 4")
        self.assertEqual(outFD7_lines[1],"Number of patches: 9")
        self.assertEqual(outFD7_lines.count("Detector: naming-convention (parameter declaration)"), 4)
        self.assertEqual(outFD7_lines.count("Detector: naming-convention (parameter uses)"), 5)
        self.assertEqual(outFD7_lines.count("Old string: uint Count"), 3)
        self.assertEqual(outFD7_lines.count("New string: uint _Count"), 3)
        self.assertEqual(outFD7_lines.count("Location start: 91"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 101"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 215"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 225"), 1)
        self.assertEqual(outFD7_lines.count("Old string: Count"), 3)
        self.assertEqual(outFD7_lines.count("New string: _Count"), 3)
        self.assertEqual(outFD7_lines.count("Old string: mod (Count)"), 1)
        self.assertEqual(outFD7_lines.count("New string: mod (_Count)"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 148"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 153"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 308"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 313"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 489"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 499"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 501"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 512"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 580"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 585"), 1)
        self.assertEqual(outFD7_lines.count("Old string: uint Number"), 1)
        self.assertEqual(outFD7_lines.count("New string: uint _Number"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 227"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 238"), 1)
        self.assertEqual(outFD7_lines.count("Old string: Number"), 1)
        self.assertEqual(outFD7_lines.count("New string: _Number"), 1)
        self.assertEqual(outFD7_lines.count("Location start: 314"), 1)
        self.assertEqual(outFD7_lines.count("Location end: 320"), 1)

    def test_naming_convention_state_variable(self):
        outFD8 = open(self.testFilePath8+".out","r")
        outFD8_lines = outFD8.readlines()
        outFD8.close()
        for i in range(len(outFD8_lines)):
            outFD8_lines[i] = outFD8_lines[i].strip()
        self.assertTrue(os.path.isfile(self.testFilePath8+".format"),"Patched .format file is not created?!")
        self.assertEqual(outFD8_lines[0],"Number of Slither results: 3")
        self.assertEqual(outFD8_lines[1],"Number of patches: 7")
        self.assertEqual(outFD8_lines.count("Detector: naming-convention (state variable declaration)"), 3)
        self.assertEqual(outFD8_lines.count("Detector: naming-convention (state variable uses)"), 4)
        self.assertEqual(outFD8_lines.count("Old string: number"), 2)
        self.assertEqual(outFD8_lines.count("New string: NUMBER"), 2)
        self.assertEqual(outFD8_lines.count("Location start: 469"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 475"), 1)
        self.assertEqual(outFD8_lines.count("Location start: 716"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 722"), 1)
        self.assertEqual(outFD8_lines.count("Old string: Count"), 3)
        self.assertEqual(outFD8_lines.count("New string: count"), 3)
        self.assertEqual(outFD8_lines.count("Location start: 547"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 552"), 1)
        self.assertEqual(outFD8_lines.count("Location start: 725"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 730"), 1)
        self.assertEqual(outFD8_lines.count("Location start: 745"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 750"), 1)
        self.assertEqual(outFD8_lines.count("Old string: Maxnum"), 2)
        self.assertEqual(outFD8_lines.count("New string: maxnum"), 2)
        self.assertEqual(outFD8_lines.count("Location start: 634"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 640"), 1)
        self.assertEqual(outFD8_lines.count("Location start: 733"), 1)
        self.assertEqual(outFD8_lines.count("Location end: 739"), 1)

if __name__ == '__main__':
    unittest.main()
