import json
import grammarDefinition as gd
from StringIO import StringIO


def readBNGLJSON(bngljson):
    with open(bngljson, 'r') as f:
        jsonDict = json.load(f)
    return jsonDict


def writeRawSection(originalMDL, buffer, tab):
    if type(originalMDL) == str:
        buffer.write(tab + originalMDL + '\n')

    elif len(originalMDL) == 0:
        return '{}'
    elif len(originalMDL) == 1:
        writeRawSection(originalMDL[0], buffer, tab)
    elif len(originalMDL) == 2:
        if type(originalMDL[0]) == list:
            for element in originalMDL:
                writeRawSection(element, buffer, tab + '\t')
        elif type(originalMDL[1]) == list:
            buffer.write('{1}{0}{{\n'.format(originalMDL[0], tab))
            writeRawSection(originalMDL[1], buffer, tab + '\t')
            buffer.write('{0}}}\n\n'.format(tab))
        elif type(originalMDL[1]) == str:
            buffer.write('{0}{1} = {2}\n'.format(tab, originalMDL[0], originalMDL[1].strip()))
    else:
        if originalMDL[1] == '@':
            buffer.write(tab + ' '.join(originalMDL) + '\n')
        else:
            for element in originalMDL:
                writeRawSection(element, buffer, tab)
            
    return buffer.getvalue()



def writeSection(originalMDL, augmentedMDLr):
    finalSection = StringIO()
    if originalMDL[0] == 'DEFINE_MOLECULES':
        pass

    else:
        return writeRawSection(originalMDL.asList(), finalSection, '') + '\n'


def readMDLr(mdlrfile):
    with open(mdlrfile, 'r') as f:
        mdlr = f.read()
    return mdlr

if __name__ == "__main__":
    finalName = 'example_expanded'
    jsonDict = readBNGLJSON('output_sbml.xml.json')
    mdlr = readMDLr('example.mdlr')
    sectionMDLR = gd.nonhashedgrammar.parseString(mdlr)
    statementMDLR = gd.statementGrammar.parseString(mdlr)
    finalMDL = StringIO()
    moleculeMDL = StringIO()
    reactionMDL = StringIO()
    outputMDL = StringIO()
    seedMDL = StringIO()
    # output statements as is
    for element in statementMDLR:
        finalMDL.write('{0} = {1}\n'.format(element[0], element[1]))

    finalMDL.write('\n')
    finalMDL.write('INCLUDE_FILE = "{0}.molecules.mdl"\n'.format(finalName))
    finalMDL.write('INCLUDE_FILE = "{0}.reactions.mdl"\n'.format(finalName))
    finalMDL.write('INCLUDE_FILE = "{0}.seed.mdl"\n\n'.format(finalName))

    # output sections using json information
    sectionOrder = {'DEFINE_MOLECULES': moleculeMDL, 'DEFINE_REACTIONS': reactionMDL, 'REACTION_DATA_OUTPUT': outputMDL, 'INSTANTIATE': seedMDL}
    for element in sectionMDLR:
        if element[0] not in sectionOrder:
            finalMDL.write(writeSection(element, jsonDict))

    finalMDL.write('INCLUDE_FILE = "{0}.output.mdl"\n'.format(finalName))

    dimensionalityDict = {}
    # molecules
    moleculeMDL.write('DEFINE_MOLECULES\n{\n')
    if 'DEFINE_MOLECULES' in sectionMDLR.keys():
        for element in sectionMDLR['DEFINE_MOLECULES']:
            writeRawSection(element, moleculeMDL, '\t')

    for molecule in jsonDict['mol_list']:
        dimensionalityDict[molecule['name']] = molecule['type']
        moleculeMDL.write('\t{0} //{1}\n\t{{ \n'.format(molecule['name'], molecule['extendedName']))
        moleculeMDL.write('\t\tDIFFUSION_CONSTANT_{0} = {1}\n'.format(molecule['type'], molecule['dif']))
        moleculeMDL.write('\t}\n')
    moleculeMDL.write('}\n')

    # reactions
    reactionMDL.write('DEFINE_REACTIONS\n{\n')
    if 'DEFINE_REACTIONS' in sectionMDLR.keys():
        for element in sectionMDLR['DEFINE_REACTIONS']:
            writeRawSection(element, reactionMDL, '\t')

    for reaction in jsonDict['rxn_list']:
        reactionMDL.write('\t{0} -> {1} [{2}]\n'.format(reaction['reactants'], reaction['products'], reaction['fwd_rate']))
    reactionMDL.write('}\n')

    # seed species
    seedMDL.write('INSTANTIATE Scene OBJECT\n{\n')
    if 'INSTANTIATE' in sectionMDLR.keys():
        for element in sectionMDLR['INSTANTIATE'][-1].asList():
            seedMDL.write('\t' + ' '.join(element[:-1]))
            seedMDL.write(writeRawSection(element[-1], seedMDL, '') + '\n')
            #
    for seed in jsonDict['rel_list']:
        print seed
        seedMDL.write('\t{0} RELEASE_SITE\n\t{{\n'.format(seed['name']))
        seedMDL.write('\t\tSHAPE = Scene.{0}\n'.format(seed['object_expr']))
        orientation = seed['orient'] if dimensionalityDict[seed['molecule']] == '2D' else ''
        seedMDL.write('\t\tMOLECULE = {0}{1}\n'.format(seed['molecule'], orientation))
        if seed['quantity_type'] == 'DENSITY':
            print dimensionalityDict
            quantity_type = 'DENSITY' if dimensionalityDict[seed['molecule']] == '2D' else 'CONCENTRATION'
        else:
            quantity_type = seed['quantity_type']
        seedMDL.write('\t\t{0} = {1}\n'.format(quantity_type, seed['quantity_expr']))
        seedMDL.write('\t\tRELEASE_PROBABILITY = 1\n'.format(seed['molecule']))
        seedMDL.write('\t}\n')

    seedMDL.write('}\n')

    # rxn_output

    outputMDL.write('REACTION_DATA_OUTPUT\n{\n')

    if 'REACTION_DATA_OUTPUT' in sectionMDLR.keys():
        for element in sectionMDLR['REACTION_DATA_OUTPUT']:
            writeRawSection(element, outputMDL, '\t')


    for obs in jsonDict['obs_list']:
        if any([x != ['0'] for x in obs['value']]):
            outputMDL.write('\t{')

            outputMDL.write(' + '.join(['COUNT[{0},WORLD]'.format(x[0]) for x in obs['value'] if x != ['0']])+ '}')

            outputMDL.write(' => "./react_data/{0}.dat"\n'.format(obs['name']))
    outputMDL.write('}\n')


    with open('{0}.main.mdl'.format(finalName), 'w') as f:
        f.write(finalMDL.getvalue())
    with open('{0}.molecules.mdl'.format(finalName), 'w') as f:
        f.write(moleculeMDL.getvalue())
    with open('{0}.reactions.mdl'.format(finalName), 'w') as f:
        f.write(reactionMDL.getvalue())
    with open('{0}.seed.mdl'.format(finalName), 'w') as f:
        f.write(seedMDL.getvalue())
    with open('{0}.output.mdl'.format(finalName), 'w') as f:
        f.write(outputMDL.getvalue())


    #print finalMDL.getvalue()
    #print finalMDL.getvalue()
