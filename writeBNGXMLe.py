from lxml import etree


def write2BNGXMLe(propertiesDict, modelName):
    #xmlns="bngexperimental"
    root = etree.Element("bngexperimental", version="1.1", name=modelName)
    #mainNode = etree.SubElement(root, "model", id=modelName)
    listOfModelProperties = etree.SubElement(root, "ListOfModelProperties")
    for element in propertiesDict['modelProperties']:
        etree.SubElement(listOfModelProperties, "Property", id=element, value=propertiesDict['modelProperties'][element])

    listOfCompartments = etree.SubElement(root, "ListOfCompartments")

    for element in propertiesDict['compartmentProperties']:
        compartmentNode = etree.SubElement(listOfCompartments,"Compartment", id=element)
        listOfCompartmentProperties = etree.SubElement(compartmentNode,"ListOfCompartmentProperties")
        for propertyEntry in propertiesDict['compartmentProperties'][element]:
            etree.SubElement(listOfCompartmentProperties, "Property", id=propertyEntry[0].strip(), value=propertyEntry[1].strip())

    listOfMoleculeTypes = etree.SubElement(root, "ListOfMoleculeTypes")

    for element in propertiesDict['moleculeProperties']:
        moleculeNode = etree.SubElement(listOfMoleculeTypes,"MoleculeType", id=element)
        listOfMoleculeProperties = etree.SubElement(moleculeNode,"ListOfMoleculeTypeProperties")
        for propertyEntry in propertiesDict['moleculeProperties'][element]:
            etree.SubElement(listOfMoleculeProperties, "Property", id=propertyEntry[0].strip(), value=propertyEntry[1].strip())

    return etree.tostring(root, pretty_print=True)


def mergeBXBXe(baseBNGXML,extendedBNGXML):
    basedoc = etree.parse(baseBNGXML).getroot()
    edoc = etree.parse(extendedBNGXML).getroot()
    basedoc.append(edoc)
    return etree.tostring(basedoc, pretty_print=True)
