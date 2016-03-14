import concurrent.futures

import fnmatch
import os
from subprocess import call, check_call
import multiprocessing as mp
import progressbar
import sys
import glob
import shutil
from os.path import expanduser,join
import pandas
import argparse
import random
import pandas
home = expanduser("~")
import csv
mcellExecutable = join(home, 'workspace', 'mcell', 'build', 'mcell')
from collections import defaultdict

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

def callMDLTest(fileName, options={}):
    '''
    run mcell on a non nfsim file
    '''
    with open(os.devnull, "w") as f:
        result = call([mcellExecutable, os.path.join(options['testpath'], 'reference', options['mdlname']),
                       '-seed', str(random.randint(1, 100000))],stdout=f)
    return result

def callMDLrTest(options):
    '''
    run mcell on an nfsim file
    '''
    with open(os.devnull, "w") as f:
        check_call([mcellExecutable, options['mdlname'],
              '-n', options['xmlname'], '-seed', str(random.randint(1, 100000))], stdout=f)

    
    return result


def generateMDLrData(testpath):
    options = {}
    #options['seed'] = 
    options['testpath'] = testpath
    options['repetitions'] = 3

    mdlfiles = getFiles(os.path.join(testpath, 'mdlr'), 'mdl')
    options['mdlname'] = [x for x in mdlfiles if 'main' in x][0]
    xmlfiles = getFiles(os.path.join(testpath, 'mdlr'), 'xml')
    options['xmlname'] = xmlfiles[0]

    postOptions = {}
    #postOptions['seed'] = options['seed']
    postOptions['dataset'] = pandas.DataFrame()

    #callMDLrTest(options)
    parallelHandling(callMDLrTest, options, processMDLrRoutput, postOptions)

    postOptions['dataset'].to_hdf('{0}DB.h5'.format('test'), '{0}_mdlr'.format(testpath))


def dummy(options):
    pass


def processMDLrRoutput(postOptions):
    trajectorydata = defaultdict(list)
    #trajectorydata['seed'] = postOptions['seed']

    with open(os.path.join('mdlr_{0}.gdat'.format(postOptions['seed'])), 'rb') as f:
        data = csv.DictReader(f, delimiter=',')
        for row in data:
            for key in row:
                if key == 'time':
                    trajectorydata['Seconds'].append(float(row[key].strip()))
                elif key not in [' ']:
                    trajectorydata[key.strip()].append(int(row[key].strip()))

    localTrajectory = pandas.DataFrame(trajectorydata)
    postOptions['dataset'] = pandas.concat([postOptions['dataset'], localTrajectory])



def parallelHandling(function, options = [], postExecutionFunction=dummy, postOptions={}):
    futures = []
    workers = mp.cpu_count() - 1
    progress = progressbar.ProgressBar(maxval=options['repetitions']).start()
    i = 0
    print 'running in {0} cores'.format(workers)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for _ in range(options['repetitions']):
            futures.append(executor.submit(function, options))
        for _ in concurrent.futures.as_completed(futures, timeout=3600):
            postExecutionFunction(postOptions)
            i += 1
            progress.update(i)
    progress.finish()



def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-t','--test',type=str,help='Test to run')
    return parser    



def saveToDataframe(result,dataframe):
    """
    Store xml-analysis results in dataframe
    """
    filename = result[0].split('/')[-1]
    filename = '.'.join(filename.split('.')[:-1]) + '_regulatory.gml'
    dataframe = dataframe.set_value(filename,'atomization',result[1])
    dataframe = dataframe.set_value(filename,'weight',result[2])
    dataframe = dataframe.set_value(filename,'compression',result[3])

if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    generateMDLrData(namespace.test)