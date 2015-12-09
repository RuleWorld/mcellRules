import argparse
import readMDL
import writeMDL


def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-i', '--input', type=str, help='input MDLr file', required=True)
    parser.add_argument('-o', '--output', type=str, help='output MDL file')
    return parser


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    bnglPath = namespace.input + '.bngl'
    finalName = namespace.output if namespace.output else namespace.input

    # mdl to bngl
    bnglStr = readMDL.constructBNGFromMDLR('example.mdlr')
    # create bngl file
    readMDL.outputBNGL(bnglStr, bnglPath)
    # bngl 2 sbml 2 json
    readMDL.bngl2json(namespace.input + '.bngl')

    # json 2 plain mdl
    mdlDict = writeMDL.constructMDL(namespace.input + '_sbml.xml.json', namespace.input, finalName)
    writeMDL.writeMDL(mdlDict, finalName)


