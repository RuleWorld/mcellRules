import xmlrpclib
import splitBNGXML


def getCannonicalLabels(seeds):
    pass

seed, _ = splitBNGXML.extractSeedBNG('example.mdlr.xml')
#print seed




proxy = xmlrpclib.ServerProxy("http://localhost:8080/RPC2")
proxy.nfsim.reset()
#print seed

initMap = {"c:a~NO_STATE!4!2,c:l~NO_STATE!3,c:l~NO_STATE!3!0,m:Lig!2!1,m:Rec!0,":1}
proxy.nfsim.initNauty(initMap)
#proxy.nfsim.step()
#proxy.nfsim.init(seed)
print '---'
print proxy.nfsim.query(2)
print '---'
print proxy.nfsim.query(1)
print proxy.nfsim.printInfo("complex")
