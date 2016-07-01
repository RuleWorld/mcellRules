from grammarDefinition import *
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import smallStructures as st
import pprint
from subprocess import call
from collections import defaultdict
import writeBNGXMLe
import os

def processParameters(statements):
    pstr = StringIO()
    pstr.write('begin parameters\n')
    for parameter in statements:
        if parameter[1][0] != '"':
            tempStr = '\t{0} {1}\n'.format(parameter[0],parameter[1]).replace('/*', '#')
            tempStr.replace('//', '#')
        else:
            continue
        pstr.write(tempStr)
    pstr.write('end parameters\n')

    return pstr.getvalue()


def createMoleculeFromPattern(moleculePattern, idx):
    tmpMolecule = st.Molecule(moleculePattern['moleculeName'], idx)
    if 'moleculeCompartment' in moleculePattern:
        tmpMolecule.compartment = moleculePattern['moleculeCompartment'][1]
    if 'components' in moleculePattern.keys():
        for idx2, component in enumerate(moleculePattern['components']):
            tmpComponent = st.Component(component['componentName'],'{0}_{1}'.format(idx,idx2))
            if 'state' in component:
                for state in component['state']:
                    if state != '':
                        tmpComponent.addState(state)
            if 'bond' in component.keys():
                for bond in component['bond']:
                    tmpComponent.addBond(bond)
            tmpMolecule.addComponent(tmpComponent)
    return tmpMolecule


def createSpeciesFromPattern(speciesPattern):
    tmpSpecies = st.Species()
    if 'speciesCompartment' in speciesPattern.keys():
        tmpSpecies.compartment = speciesPattern['speciesCompartment'][1]
    for idx, element in enumerate(speciesPattern['speciesPattern']):
        tmpSpecies.addMolecule(createMoleculeFromPattern(element, idx))
    return tmpSpecies


def processMolecules(molecules):
    mstr = StringIO()
    moleculeList = []
    mstr.write('begin molecule types\n')
    for idx, molecule in enumerate(molecules):
        tmpMolecule = createMoleculeFromPattern(molecule[0], idx)
        moleculeList.append((tmpMolecule.name,str(tmpMolecule)))
        mstr.write('\t{0}\n'.format(tmpMolecule.str2()))
    mstr.write('end molecule types\n')
    return mstr.getvalue(), moleculeList


def processInitCompartments(initializations):
    sstr = StringIO()
    cstr = StringIO()
    sstr.write('begin seed species\n')
    cstr.write('begin compartments\n')

    for initialization in initializations:
        #print initialization.keys()
        if 'name' in initialization.keys():
            tmpSpecies = None
            initialConditions = 0
            for entry in initialization['entries']:
                if entry[0] == 'MOLECULE':
                    pattern = species_definition.parseString(entry[1])
                    tmpSpecies = createSpeciesFromPattern(pattern[0])
                elif entry[0] == 'NUMBER_TO_RELEASE':
                    initialConditions = entry[1]
            sstr.write('\t {0} {1}\n'.format(str(tmpSpecies),initialConditions))
        else:
            optionDict = {'parent': '', 'name': initialization['compartmentName']}
            for option in initialization['compartmentOptions'][0]:
                if len(option) > 0:
                    if option[0] == 'MEMBRANE':
                        
                        tmp = option[1].strip()
                        optionDict['membrane'] = tmp.split(' ')[0]
                    elif option[0] == 'PARENT':
                        tmp = option[1].strip()
                        optionDict['parent'] = tmp
            if 'membrane' in optionDict:
                cstr.write('\t{0} 2 1 {1}\n'.format(optionDict['membrane'], optionDict['parent']))
                cstr.write('\t{0} 3 1 {1}\n'.format(optionDict['name'], optionDict['membrane']))
            else:
                tmp = '{0} 3 1 {1}'.format(optionDict['name'], optionDict['parent'])
                tmp = tmp.strip()
                cstr.write('\t{0}\n'.format(tmp))

    sstr.write('end seed species\n')
    cstr.write('end compartments\n')
    return sstr.getvalue(), cstr.getvalue()


def processObservables(observables):
    ostr = StringIO()
    ostr.write('begin observables\n')
    for observable in observables:
        if 'patterns' in observable.keys() and 'outputfile' in observable.keys():
            tmpObservable = '\tMolecules '
            tmpObservable += '{0} '.format(observable['outputfile'].split('/')[-1].split('.')[0])
            patternList = []
            for pattern in observable['patterns']:
                patternList.append(str(createSpeciesFromPattern(pattern['speciesPattern'])))
            tmpObservable +=  ', '.join(patternList)
            ostr.write(tmpObservable + '\n')
        elif 'obskey' in observable.keys():
            tmpObservable = '\t{0} '.format(observable['obskey'])
            tmpObservable += '{0} '.format(observable['obsname'])
            patternList = []
            for pattern in observable['obspatterns']:
                patternList.append(str(createSpeciesFromPattern(pattern)))
            tmpObservable +=  ', '.join(patternList)
            ostr.write(tmpObservable + '\n')

    ostr.write('end observables\n')
    return ostr.getvalue()

def processMTObservables(moleculeTypes):
    '''
    creates a list of observables from just molecule types
    '''
    ostr = StringIO()
    raise Exception

    ostr.write('begin observables\n')
    for moleculeType in moleculeTypes:
        ostr.write('\t Species {0} {1}\n'.format(moleculeType[0], moleculeType[1]))
    ostr.write('end observables\n')


    return ostr.getvalue()


def processReactionRules(rules):
    rStr = StringIO()
    rStr.write('begin reaction rules\n')
    for rule in rules:
        tmpRule = st.Rule()
        for pattern in rule['reactants']:
            tmpRule.addReactant(createSpeciesFromPattern(pattern))
        for pattern in rule['products']:
            tmpRule.addProduct(createSpeciesFromPattern(pattern))
        for rate in rule['rate']:
            tmpRule.addRate(rate)
        rStr.write('\t{0}\n'.format(str(tmpRule)))

    rStr.write('end reaction rules\n')
    return rStr.getvalue()


def processDiffussionElements(parameters, extendedData):
    '''
    extract the list of properties associated to molecule types and compartment objects. right now this information
    will be encoded into the bng-exml spec. It also extracts some predetermined model properties. 
    '''
    modelProperties = {}
    moleculeProperties = defaultdict(list)
    compartmentProperties = defaultdict(list)

    #for parameter in parameters:
    #    if parameter[0] in ['TEMPERATURE']:
    #        modelProperties[parameter[0]] = parameter[1]

    for parameter in extendedData['system']:
        modelProperties[parameter[0].strip()] = parameter[1].strip()



    
    for molecule in extendedData['molecules']:
        if 'moleculeParameters' in molecule[1]:
            for propertyValue in molecule[1]['moleculeParameters']:
                data = {'name':propertyValue[1].strip(), 'parameters': []}
                moleculeProperties[molecule[0][0]].append((propertyValue[0], data))
        if 'diffusionFunction' in molecule[1]:
            if 'function' in molecule[1]['diffusionFunction'].keys():
                parameters = molecule[1]['diffusionFunction'][1]['parameters']
                data = {'name': '"{0}"'.format(molecule[1]['diffusionFunction'][1]['functionName']), 
                'parameters':[(x['key'], x['value']) for x in parameters]}
            else:
                data = {'name':molecule[1]['diffusionFunction'][1].strip(), 'parameters': []}
            #moleculeProperties[molecule[0][0]].append((molecule[1]['diffusionFunction'][0], data))
            if '3D' in molecule[1]['diffusionFunction'].keys():
                dimensionality = {'name':'3','parameters':[]}
            if '2D' in molecule[1]['diffusionFunction'].keys():
                dimensionality = {'name':'2','parameters':[]}

            moleculeProperties[molecule[0][0]].append(('diffusion_function', data))
            moleculeProperties[molecule[0][0]].append(('dimensionality', dimensionality))

    for seed in extendedData['initialization']:
        if 'compartmentName' in seed.keys():
            membrane = ''
            membrane_properties = []
            for element in seed['compartmentOptions'][0]:
                # skip stuff already covered by normal cbng
                if element[0] in ['PARENT']:
                    continue
                if element[0] == 'MEMBRANE':
                    membrane = element[1].strip().split(' ')[0]
                elif element[0].startswith('MEMBRANE'):
                    membrane_properties.append((element[0].split('_')[1], element[1].strip()))

                else:
                    compartmentProperties[seed['compartmentName']].append((element[0], element[1]))
            if membrane != '' and len(membrane_properties) > 0:
                compartmentProperties[membrane] = membrane_properties
        #if seed[1] not in ['RELEASE_SITE']:

    return {'modelProperties':modelProperties, 'moleculeProperties': moleculeProperties, 
            'compartmentProperties': compartmentProperties}

def writeDefaultFunctions():
    defaultFunctions = StringIO()

    defaultFunctions.write('begin functions\n')
    defaultFunctions.write('\teinstein_stokes(p_kb, p_t, p_rs, p_mu)= p_kb*p_t/(6*3.141592*p_mu*p_rs)\n')
    defaultFunctions.write('\tsaffman_delbruck(p_kb, p_t, p_rc, p_mu, p_mu_ex, p_gamma, p_h) = p_kb*p_t*log((p_mu*p_h/(p_rc*p_mu_ex)-p_gamma))/(4*3.141592*p_mu*p_h)\n')
    defaultFunctions.write('end functions\n')

    return defaultFunctions.getvalue()

def constructBNGFromMDLR(mdlrPath,nfsimFlag=False, separateSpatial=True):
    '''
    initializes a bngl file and an extended-bng-xml file with a MDLr file description
    '''
    with open(mdlrPath, 'r') as f:
        mdlr = f.read()

    statements = statementGrammar.parseString(mdlr)

    sections = grammar.parseString(mdlr)
    finalBNGLStr = StringIO()
    finalBNGLStr.write('begin model\n')
    parameterStr = processParameters(statements)
    moleculeStr,moleculeList = processMolecules(sections['molecules'])
    seedspecies, compartments = processInitCompartments(sections['initialization']['entries'])
    if not nfsimFlag:
        observables = processObservables(sections['observables'])
    else:
        observables = processObservables(sections['observables'])
        #observables = processMTObservables(moleculeList)
    reactions = processReactionRules(sections['reactions'])

    #functions = writeDefaultFunctions()

    finalBNGLStr.write(parameterStr)
    finalBNGLStr.write(moleculeStr)
    finalBNGLStr.write(compartments)
    finalBNGLStr.write(seedspecies)
    finalBNGLStr.write(observables)
    #finalBNGLStr.write(functions)
    #finalBNGLStr.write('begin observables\nend observables\n')
    finalBNGLStr.write(reactions)
    finalBNGLStr.write('end model\n')

    #add processing actions
    finalBNGLStr.write('generate_network({overwrite=>1})\n')
    finalBNGLStr.write('writeSBML()\n')

    '''
    eventually this stuff should be integrated into bionetgen proper
    '''
    if separateSpatial:

        extendedData = {}
        if 'systemConstants' in sections.keys():
            extendedData['system'] = sections['systemConstants']
        else:
            extendedData['system'] = []
        extendedData['molecules'] = sections['molecules']
        extendedData['initialization'] = sections['initialization']['entries']
        propertiesDict = processDiffussionElements(statements, extendedData)
        bngxmle = writeBNGXMLe.write2BNGXMLe(propertiesDict, mdlrPath.split(os.sep)[-1])

    return {'bnglstr':finalBNGLStr.getvalue(), 'bngxmlestr':bngxmle}


def bngl2json(bnglFile):
    call(['bngdev',bnglFile])
    sbmlName = '.'.join(bnglFile.split('.')[:-1]) + '_sbml.xml'
    print(sbmlName)
    call(['./sbml2json','-i', sbmlName])


def outputBNGL(bnglStr, bnglPath):
    with open(bnglPath, 'w') as f:
        f.write(bnglStr)


if __name__ == "__main__":
    
    #with open('example.mdlr', 'r') as f:
    #    mldr = f.read()
    #statements = statementGrammar.parseString(mldr)
    #sections = grammar.parseString(mldr)
    #bnglStr = constructBNGFromMDLR(statements, sections)
    
    bnglStr = constructBNGFromMDLR('example.mdlr')
    bnglPath = 'output.bngl'
    #with open(bnglFile,'w') as f:
    #    f.write(bnglStr)
    outputBNGL(bnglStr, bnglPath)

    bngl2json(bnglFile)


