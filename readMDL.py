from grammarDefinition import *
from StringIO import StringIO
import smallStructures as st
import pprint


def processParameters(statements):
    pstr = StringIO()
    pstr.write('begin parameters\n')
    for parameter in statements:
        if parameter[1][0] != '"':
            tempStr = '\t{0} {1}\n'.format(parameter[0],parameter[1]).replace('/*', '#')
        else:
            continue
        pstr.write(tempStr)
    pstr.write('end parameters\n')

    return pstr.getvalue()


def createMoleculeFromPattern(moleculePattern, idx):
    tmpMolecule = st.Molecule(moleculePattern['moleculeName'], idx)
    if 'moleculeCompartment' in moleculePattern:
        tmpMolecule.compartment = moleculePattern['moleculeCompartment'][1]
    for idx2, component in enumerate(moleculePattern['components']):
        tmpComponent = st.Component(component['componentName'],'{0}_{1}'.format(idx,idx2))
        if 'state' in component:
            for state in component['state'][1:]:
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
    mstr.write('begin molecule types\n')
    for idx, molecule in enumerate(molecules):
        tmpMolecule = createMoleculeFromPattern(molecule[0], idx)
        mstr.write('\t{0}\n'.format(tmpMolecule.str2()))
    mstr.write('end molecule types\n')
    return mstr.getvalue()

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
            tmpObservable = '\tSpecies '
            tmpObservable += '{0} '.format(observable['outputfile'].split('/')[-1].split('.')[0])
            patternList = []
            for pattern in observable['patterns']:
                patternList.append(str(createSpeciesFromPattern(pattern['speciesPattern'])))
            tmpObservable +=  ', '.join(patternList)
            ostr.write(tmpObservable + '\n')

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
    
def constructBNGFromMDLR(statements, sections):

    finalBNGLStr = StringIO()
    parameterStr = processParameters(statements)
    moleculeStr = processMolecules(sections['molecules'])
    seedspecies, compartments = processInitCompartments(sections['initialization']['entries'])
    observables = processObservables(sections['observables'])
    reactions = processReactionRules(sections['reactions'])

    finalBNGLStr.write(parameterStr)
    finalBNGLStr.write(moleculeStr)
    finalBNGLStr.write(compartments)
    finalBNGLStr.write(seedspecies)
    finalBNGLStr.write(observables)
    finalBNGLStr.write(reactions)

    return finalBNGLStr.getvalue()



    #construct molecules


        #tmpmolecule = st.Molecule(mo)


if __name__ == "__main__":
    with open('example.mdlr', 'r') as f:
        mldr = f.read()

    #s = species_definition.parseString('@PM::Lig(l!+~P,l!1).Rec(r!1)@EC')
    #pprint.pprint(s[0]['speciesPattern'][0]['components'][0])
    #print '+++', molecule_definition.parseString('Rec(a~0~P)')
    #print '---', species_definition.parseString('Rec(a!2~0).Lig(l!2,l!+)')
    #pprint.pprint(reaction_definition.parseString('Rec(a!2~0).Lig(l!2,l!+) <-> Rec(a) + Lig(l,l!+) [4,3]').asList())
    #print '/////'
    statements = statementGrammar.parseString(mldr)
    sections = grammar.parseString(mldr)

    bnglStr = constructBNGFromMDLR(statements, sections)
    with open('output.bngl','w') as f:
        f.write(bnglStr)
