import concurrent.futures
import shutil
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
import misc

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

def callMDLTest(options):
    '''
    run mcell on a non nfsim file
    '''
    seed = str(random.randint(1, 1000000))
    
    outputdir = os.path.join('testdata', str(seed))
    os.makedirs(outputdir)
    #os.chdir(seed)

    with open(os.devnull, "w") as f:
        result = call([mcellExecutable, os.path.join(options['testpath'], 'reference', options['mdlname']),
                       '-seed', seed], stdout=f, cwd=outputdir)
    #os.chdir('..')        
    return outputdir

def callMDLrTest(options):
    '''
    run mcell on an nfsim file
    '''
    seed = str(random.randint(1, 1000000))
    outputdir = os.path.join('testdata', str(seed))
    os.makedirs(outputdir)
    #os.chdir(seed)
    with open(os.devnull, "w") as f:
        check_call([mcellExecutable, os.path.join('..',options['mdlname']),
              '-n', os.path.join('..',options['xmlname']), '-seed', seed], stdout=f, cwd=outputdir)
    #os.chdir('..')

    
    return outputdir


def generateMDLrData(testpath, databasename, repetitions):

    #repetitions = 50
    options = {}
    #options['seed'] = 
    options['testpath'] = testpath
    options['repetitions'] = repetitions

    mdlfiles = getFiles(os.path.join(testpath, 'mdlr'), 'mdl')
    options['mdlname'] = [x for x in mdlfiles if 'main' in x][0]
    xmlfiles = getFiles(os.path.join(testpath, 'mdlr'), 'xml')
    options['xmlname'] = xmlfiles[0]
    #options['workerIdx'] = '00'
    #callMDLrTest(options)
    postOptions = {}
    #postOptions['seed'] = options['seed']
    postOptions['dataset'] = pandas.DataFrame()

    options2 = {}
    options2['testpath'] = testpath
    options2['repetitions'] = repetitions
    mdlfiles = getFiles(os.path.join(testpath,'reference'), 'mdl')
    options2['mdlname'] = [x for x in mdlfiles if 'main' in x][0]
    print 'process MDL files...'
    parallelHandling(callMDLTest, options2, processMDLoutput,postOptions)
    print 'processing MDLr files...'
    parallelHandling(callMDLrTest, options, processMDLroutput, postOptions)

    postOptions['dataset'].to_hdf('{0}DB.h5'.format(testpath), testpath,format='table',append=True)


def dummy(options):
    pass


def processMDLroutput(postOptions):
    #trajectorydata['seed'] = postOptions['seed']
    gdatFiles = getFiles(postOptions['workerIdx'],'gdat')
    trajectorydata = misc.processMDLrData(gdatFiles[0], postOptions['workerIdx'])

    localTrajectory = pandas.DataFrame(trajectorydata)
    postOptions['dataset'] = pandas.concat([postOptions['dataset'], localTrajectory])
    shutil.rmtree(postOptions['workerIdx'])

def processMDLoutput(postOptions):
    #trajectorydata['seed'] = postOptions['seed']
    gdatFiles = getFiles(postOptions['workerIdx'],'txt')
    trajectorydata = misc.processMDLData(gdatFiles[0], postOptions['workerIdx'])

    localTrajectory = pandas.DataFrame(trajectorydata)
    postOptions['dataset'] = pandas.concat([postOptions['dataset'], localTrajectory])
    shutil.rmtree(postOptions['workerIdx'])


def parallelHandling(function, options = {}, postExecutionFunction=dummy, postOptions={}):
    futures = []
    workers = mp.cpu_count() - 1
    progress = progressbar.ProgressBar(maxval=options['repetitions']).start()
    i = 0
    print 'running in {0} cores'.format(workers)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for idx in range(options['repetitions']):
            options['workerIdx'] = str(idx)
            futures.append(executor.submit(function, options))
        for future in concurrent.futures.as_completed(futures, timeout=3600):
            postOptions['workerIdx'] = future.result()
            postExecutionFunction(postOptions)
            i += 1
            progress.update(i)
    progress.finish()



def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-t','--test',type=str,help='Test to run')
    parser.add_argument('-r','--repetitions',type=int, help='number of separate stochastic trajectories')
    return parser    



if __name__ == "__main__":
    databasename = 'timeseries4'
    parser = defineConsole()
    namespace = parser.parse_args()
    generateMDLrData(namespace.test, databasename, namespace.repetitions)