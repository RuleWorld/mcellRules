from ctypes import *


class queryResultsStruct(Structure):
    _fields_ = [("numOfResults", c_int),
                ("results", POINTER(c_char_p))]


class NFSim:
    def __init__(self, libPath):
        self.lib = cdll.LoadLibrary(libPath)

    def initNFsim(self, fileName, verbose):
        """
        inits an nfsim object with a given xml file and a verbosity setting 
        """
        self.lib.setupNFSim_c(fileName, verbose)

    def resetSystem(self):
        """
        Resets an nfsim system to having no seeds species
        """
        return self.lib.resetSystem_c()


    def initSystemNauty(self, initDict):
        """
        Initializes an nfsim simulation with a given nfsim dictionary with the species in nauty format
        """
        species = [x for x in initDict]
        seeds = [initDict[x] for x in initDict]

        CArray = c_char_p * len(initDict)
        speciesCArray = CArray(*species)
        seedCArray = CArray(*seeds) 
        return self.lib.initSystemNauty_c(speciesCArray, seedCArray, len(initDict))


    def initSystemXML(self, initXML):
        """
        Initializes an nfsim simulation with a given seed species XML string
        """
        return self.lib.initSystemXML_c(initXML)


    def querySystemStatus(self, option):
        """
        returns all species that participate in active reactions with numReactants reactants
        """
        #self.lib.querySystemStatus_c.restype = queryResultsStruct
        
        mem = self.lib.systemStatus_createContainer()
        #queryResults = self.lib.querySystemStatus_c(option, mem)
        self.lib.querySystemStatus_c.argtypes = [c_char_p, c_void_p]
        self.lib.map_get.restype = c_char_p

        key = c_char_p(option)
        self.lib.querySystemStatus_c(key,mem)
        #results = [queryResults.results[i] for i in range(0, queryResults.numOfResults)]
        results = []
        for idx in range(0, self.lib.systemStatus_querySize(mem)):
            #XXX:ideally i would like to returns all key values but that will require a lil more work on teh wrapper side
            partialResults = self.lib.systemStatus_queryGet(mem, idx)
            results.append(self.lib.map_get(partialResults,"label"))
        return sorted(results, key=len)




if __name__ == "__main__":
    nfsim = NFSim('./debug/libnfsim_c.so')

    nfsim.initNFsim("cbngl_test_empty.xml", 0)
    nfsim.resetSystem()
    #nfsim.initSystemNauty({"c:a~NO_STATE!4!2,c:l~NO_STATE!3,c:l~NO_STATE!3!0,m:Lig!2!1,m:Rec!0":1})
    #nfsim.initSystemNauty({"c:a~NO_STATE!4!2,c:l~NO_STATE!3,c:l~NO_STATE!3!0,m:Lig!1!2,m:Rec!0,":1})
    #print '---', nfsim.querySystemStatus("observables")
    nfsim.initSystemNauty({"c:l~NO_STATE!3!1,c:r~NO_STATE!2!0,m:L@EC!1,m:R@PM!0,":1})
    print '----', nfsim.querySystemStatus("complex")
    
    
    """
    nfsim.initSystemXML('''<Model><ListOfSpecies><Species id="S1"  concentration="1" name="@PM::Lig(l!1,l).Rec(a!1)" compartment="PM">
        <ListOfMolecules>
          <Molecule id="S1_M1" name="Lig" compartment="PM">
            <ListOfComponents>
              <Component id="S1_M1_C1" name="l" numberOfBonds="0"/>
              <Component id="S1_M1_C2" name="l" numberOfBonds="1"/>
            </ListOfComponents>
          </Molecule>
          <Molecule id="S1_M2" name="Rec" compartment="PM">
            <ListOfComponents>
              <Component id="S1_M2_C1" name="a" numberOfBonds="1"/>
            </ListOfComponents>
          </Molecule>
        </ListOfMolecules>
        <ListOfBonds>
          <Bond id="S1_B1" site1="S1_M1_C1" site2="S1_M2_C1"/>
        </ListOfBonds>
      </Species></ListOfSpecies></Model>''')
    """
