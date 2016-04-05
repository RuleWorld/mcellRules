import argparse
import fnmatch
import os
import pandas

def getFiles(directory, extension):
    """
    Gets a list of <*.extension> files. include subdirectories and return the absolute 
    path. also sorts by size.
    """
    matches = []
    for root, _, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, '*.{0}'.format(extension)):
            matches.append([os.path.join(os.path.abspath(root), filename), os.path.getsize(os.path.join(root, filename))])

    #sort by size
    matches.sort(key=lambda filename: filename[1], reverse=False)
    
    matches = [x[0] for x in matches]

    return matches


def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-w','--workDirectory',type=str, help='the folder where the output files will be placed', default=os.getcwd())
    parser.add_argument('-o','--outputfile', type=str)
    return parser    




if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    pandalist = getFiles(namespace.workDirectory, 'h5')
    pandasArray = []
    for df in pandalist:
        pandasArray.append(pandas.read_hdf(df))
    trajectorydataset = pandas.DataFrame()
    for df in pandasArray:
        trajectorydataset = pandas.concat([trajectorydataset, df])

    trajectorydataset.to_hdf(namespace.outputfile, 'results')
