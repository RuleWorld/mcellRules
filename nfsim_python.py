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
        self.lib.querySystemStatus_c.restype = queryResultsStruct
        queryResults = self.lib.querySystemStatus_c(option)
        results = [queryResults.results[i] for i in range(0, queryResults.numOfResults)]
        return sorted(results, key=len)




if __name__ == "__main__":
    nfsim = NFSim('./lib/libnfsim_c.so')

    nfsim.initNFsim("example.mdlr.xml_total.xml", 0)
    nfsim.resetSystem()
    nfsim.initSystemNauty({"c:a~NO_STATE!4!2,c:l~NO_STATE!3,c:l~NO_STATE!3!0,m:Lig!2!1,m:Rec!0":1})
    print nfsim.querySystemStatus("complex")
