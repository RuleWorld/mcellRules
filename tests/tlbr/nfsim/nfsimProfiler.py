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
import pandas as pd
import argparse
import random
home = expanduser("~")
import csv
nfsimExecutable = join(home, 'workspace', 'RuleWorld', 'nfsim', 'build', 'NFsim')
#mcellExecutable = join(home, 'workspace', 'mcell', 'debug', 'mcell')
from collections import defaultdict
import re
import numpy as np

def callNFSim(options):

    outputdir = os.path.join(options['workdir'])

    seed = str(random.randint(1, 1000000))
    with open(os.devnull, "w") as f:
        result = call([nfsimExecutable, '-xml', os.path.join('beta_{0}'.format(options['beta']), 'tlbr.xml'), '-cb', 
                      '-sim', '10', '-osteps', '50', '-o', '{0}/output_{1}'.format(outputdir, seed),
                      '-seed', '{0}'.format(seed)], stdout=f)

    return seed


def generateNFSimData(outputdir, repetitions, beta):
    options = {}
    postOptions = {}
    options['beta'] = beta
    seed = str(random.randint(1, 1000000))
    options['workdir'] = os.path.join(outputdir, seed)
    os.makedirs(options['workdir'])
    try:
        os.makedirs(os.path.join(outputdir, 'partial',str(beta)))
    except OSError:
        pass

    options['repetitions'] = repetitions

    postOptions['workdir'] = options['workdir']
    postOptions['dataset'] = pd.DataFrame()
    
    parallelHandling(callNFSim, options, processGDATOutput, postOptions)
    partialresultdir = os.path.join(outputdir,'partial',str(beta))
    postOptions['dataset'].to_hdf('{0}/{1}DB_.h5'.format(partialresultdir, random.randint(1,99999999)), 'nfsim',format='table',append=True)
    shutil.rmtree(options['workdir'])



def loadResults(fileName, split):
    try:
        with open(fileName) as dataInput:
            timeCourse = []
            # remove spaces
            line = dataInput.readline().strip()
            headers = re.sub('\s+', ' ', line).split(split)

            for line in dataInput:
                nline = re.sub('\s+', ' ', line.strip()).split(' ')
                try:
                    timeCourse.append([float(x) for x in nline])
                except:
                    print '++++', nline
        return headers, np.array(timeCourse)
    except IOError:
        print 'no file'
        return [], []


def processGDATOutput(postOptions):
    inputdir = os.path.join(postOptions['workdir'])
    gdatFile = os.path.join(inputdir, 'output_{0}'.format(postOptions['workerIdx']))

    headers, timeCourse = loadResults(gdatFile, ' ')
    headers = headers[1:]
    localTrajectory = pd.DataFrame(timeCourse, columns=headers)
    postOptions['dataset'] = pd.concat([postOptions['dataset'], localTrajectory], ignore_index=True)


def dummy(postOptions):
    pass

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
    parser.add_argument('-w','--workDirectory',type=str, help='the folder where the output files will be placed', default=os.getcwd())
    parser.add_argument('-r','--repetitions',type=int, help='number of trajectories to be simulated', default=4)
    parser.add_argument('-b','--beta',type=str, help='beta parameter', default=50)

    return parser    



if __name__ == "__main__":
    databasename = 'timeseries4'
    parser = defineConsole()
    namespace = parser.parse_args()
    generateNFSimData(namespace.workDirectory, namespace.repetitions, namespace.beta)