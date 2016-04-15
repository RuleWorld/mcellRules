from lxml import etree


def createPropertyNode(parentNode, key, value):
    if value.startswith('"'):
        propertyNode = etree.SubElement(parentNode, "Property", id=key, value=value.strip('"'), type="str")
    else:
        propertyNode = etree.SubElement(parentNode, "Property", id=key, value=value, type="num")
    return propertyNode
def write2BNGXMLe(propertiesDict, modelName):
    '''
    creates a bng-xml v1.1 spec from model properties
    '''
    #xmlns="bngexperimental"
    root = etree.Element("bngexperimental", version="1.1", name=modelName)
    #mainNode = etree.SubElement(root, "model", id=modelName)
    if len(propertiesDict['modelProperties']) > 0:
        listOfModelProperties = etree.SubElement(root, "ListOfProperties")
        for element in propertiesDict['modelProperties']:
            #etree.SubElement(listOfModelProperties, "Property", id=element.strip().lower(), value=propertiesDict['modelProperties'][element].strip())
            createPropertyNode(listOfModelProperties, element.strip().lower(), propertiesDict['modelProperties'][element].strip())

    listOfCompartments = etree.SubElement(root, "ListOfCompartments")

    for element in propertiesDict['compartmentProperties']:
        compartmentNode = etree.SubElement(listOfCompartments,"Compartment", id=element)
        listOfCompartmentProperties = etree.SubElement(compartmentNode,"ListOfProperties")
        for propertyEntry in propertiesDict['compartmentProperties'][element]:
            #etree.SubElement(listOfCompartmentProperties, "Property", id=propertyEntry[0].strip().lower(), value=propertyEntry[1].strip())
            createPropertyNode(listOfCompartmentProperties, propertyEntry[0].strip().lower(), propertyEntry[1].strip())

    listOfMoleculeTypes = etree.SubElement(root, "ListOfMoleculeTypes")

    for element in propertiesDict['moleculeProperties']:
        moleculeNode = etree.SubElement(listOfMoleculeTypes,"MoleculeType", id=element)
        listOfMoleculeProperties = etree.SubElement(moleculeNode,"ListOfProperties")
        for propertyEntry in propertiesDict['moleculeProperties'][element]:
            propertyNode = createPropertyNode(listOfMoleculeProperties, propertyEntry[0].strip().lower(), propertyEntry[1]['name'].strip())
            if len(propertyEntry[1]['parameters']) > 0:
                sublistOfMoleculeProperties = etree.SubElement(propertyNode,"ListOfProperties")
                #propertyNode = etree.SubElement(listOfMoleculeProperties, "Property", id=propertyEntry[0].strip().lower(), value=propertyEntry[1]['name'].strip())
                for parameter in propertyEntry[1]['parameters']:
                    etree.SubElement(sublistOfMoleculeProperties, "Property",id=parameter[0],value=parameter[1])

    return etree.tostring(root, pretty_print=True)


def mergeBXBXe(baseBNGXML, extendedBNGXML):
    '''
    temporary method to concatenate a bng-xml 1.0 and bng-xml 1.1 definition
    '''
    basedoc = etree.parse(baseBNGXML).getroot()
    edoc = etree.parse(extendedBNGXML).getroot()
    basedoc.append(edoc)
    return etree.tostring(basedoc, pretty_print=True)
