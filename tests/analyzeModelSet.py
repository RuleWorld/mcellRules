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
#mcellExecutable = join(home, 'workspace', 'mcell', 'debug', 'mcell')
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
    
    outputdir = os.path.join(options['workdir'], str(seed))
    try:
        os.makedirs(outputdir)
    except OSError:
        pass
    #os.chdir(seed)

    with open(os.devnull, "w") as f:
        result = call([mcellExecutable, os.path.join(options['testpath'], 'reference', options['mdlname']),
                       '-seed', seed], stdout=f, cwd=outputdir)
    #os.chdir('..')        
    return seed

def callMDLrTest(options):
    '''
    run mcell on an nfsim file
    '''
    seed = str(random.randint(1, 1000000))
    outputdir = os.path.join(options['workdir'], str(seed))
    try:
        os.makedirs(outputdir)
    except OSError:
        pass
    #os.chdir(seed)
    with open(os.devnull, "w") as f:
        call([mcellExecutable, os.path.join('..',options['mdlname']),
              '-n', os.path.join('..',options['xmlname']), '-seed', seed], stdout=f, cwd=outputdir)
    #os.chdir('..')

    
    return seed


def generateMDLrData(testpath, databasename, repetitions, outputdir):

    #repetitions = 50
    options = {}
    #options['seed'] = 

    mdlfiles = getFiles(os.path.join(testpath, 'mdlr'), 'mdl')
    postOptions = {}
    #postOptions['seed'] = options['seed']
    postOptions['dataset'] = pandas.DataFrame()
    postOptions['workdir'] = os.path.join(outputdir, testpath)

    if len(mdlfiles) > 0:
        options['testpath'] = testpath
        options['repetitions'] = repetitions
        options['mdlname'] = [x for x in mdlfiles if 'main' in x][0]
        xmlfiles = getFiles(os.path.join(testpath, 'mdlr'), 'xml')
        options['xmlname'] = xmlfiles[0]
        options['workdir'] = os.path.join(outputdir, testpath)
        print 'processing MDLr files...'
        parallelHandling(callMDLrTest, options, processMDLroutput, postOptions)

    options2 = {}

    mdlfiles = getFiles(os.path.join(testpath,'reference'), 'mdl')
    if len(mdlfiles) > 0:
        options2['testpath'] = testpath
        options2['repetitions'] = repetitions
        options2['workdir'] = os.path.join(outputdir, testpath)
        options2['mdlname'] = [x for x in mdlfiles if 'main' in x][0]
        if len(mdlfiles) > 0:
            print 'process MDL files...'
            parallelHandling(callMDLTest, options2, processMDLoutput,postOptions)

    partialresultdir = os.path.join(outputdir, testpath, 'partial')
    try:
        os.makedirs(partialresultdir)
    except OSError:
        pass
    postOptions['dataset'].to_hdf('{0}/{1}DB_.h5'.format(partialresultdir, random.randint(1,99999999)), testpath,format='table',append=True)


def dummy(options):
    pass


def processMDLroutput(postOptions):
    #trajectorydata['seed'] = postOptions['seed']
    inputdir = os.path.join(postOptions['workdir'], postOptions['workerIdx'])
    gdatFiles = getFiles(inputdir,'gdat')
    trajectorydata = misc.processMDLrData(gdatFiles[0], postOptions['workerIdx'])

    localTrajectory = pandas.DataFrame(trajectorydata)
    postOptions['dataset'] = pandas.concat([postOptions['dataset'], localTrajectory])
    shutil.rmtree(inputdir)

def processMDLoutput(postOptions):
    #trajectorydata['seed'] = postOptions['seed']
    inputdir = os.path.join(postOptions['workdir'], postOptions['workerIdx'])
    #print inputdir
    gdatFiles = getFiles(inputdir, 'txt')

    trajectorydata = misc.processMDLData(gdatFiles[0], postOptions['workerIdx'])

    localTrajectory = pandas.DataFrame(trajectorydata)
    postOptions['dataset'] = pandas.concat([postOptions['dataset'], localTrajectory])
    shutil.rmtree(inputdir)


def parallelHandling(function, options = {}, postExecutionFunction=dummy, postOptions={}):
    futures = []
    workers = mp.cpu_count() 
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
    parser.add_argument('-w','--workDirectory',type=str, help='the folder where the output files will be placed', default=os.getcwd())
    return parser    



if __name__ == "__main__":
    databasename = 'timeseries4'
    parser = defineConsole()
    namespace = parser.parse_args()
    generateMDLrData(namespace.test, databasename, namespace.repetitions, outputdir=namespace.workDirectory)
