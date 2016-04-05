import pandas
import os
from collections import defaultdict
import csv
import subprocess
import progressbar
import random
from scipy import stats
import numpy as np
import argparse

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def MDLTrajectoryGeneration(params):
    mcellbinary = params['mcell']
    testname = params['testname']
    repetitions = params['repetitions']
    trajectorydataset = pandas.DataFrame()
    progress = progressbar.ProgressBar()
    print('Generating MDL data..')
    for idx in progress(range(repetitions)):



        with open(os.devnull, "w") as fnull:
            subprocess.check_call([mcellbinary, os.path.join(testname, 'reference', 'vol_example.main.mdl'),
                                   '-seed', str(random.randint(1, 100000))], stdout=fnull)

        trajectorydata = processMDLData('counts.txt', idx)
        localTrajectory = pandas.DataFrame(trajectorydata)

        trajectorydataset = pandas.concat([trajectorydataset, localTrajectory])
    return trajectorydataset

def processMDLData(fileName, iteration):
    trajectorydata = defaultdict(list)
    trajectorydata['iteration'] = iteration.split('/')[-1]
    with open(fileName, 'rb') as f:
        data = csv.DictReader(f, delimiter=' ')

        for row in data:
            for key in row:
                if key == 'Seconds':
                    continue
                    #trajectorydata[key].append(float(row[key]))
                else:
                    trajectorydata['Seconds'].append(float(row['Seconds']))
                    trajectorydata['Observable'].append(key)
                    trajectorydata['Value'].append(int(row[key]))
                    trajectorydata['Origin'].append('Standard MCell')
    return trajectorydata

def MDLRTrajectoryGeneration(params, trajectorydataset):
    mcellbinary = params['mcell']
    testname = params['testname']
    repetitions = params['repetitions']
    #trajectorydataset = pandas.DataFrame()
    progress = progressbar.ProgressBar()
    print('Generating MDLr data..')
    for idx in progress(range(repetitions)):


        with open(os.devnull, "w") as fnull:
            subprocess.check_call([mcellbinary, os.path.join(testname, 'mdlr', 'simple.main.mdl'),
                                   '-n', os.path.join(testname, 'mdlr', 'vol_example.mdlr_total.xml'),
                                   '-seed', str(random.randint(1, 100000))], stdout=fnull, stderr=fnull)
        '''
        with open(os.path.join(testname, 'mdlr', 'vol_example.mdlr_total.xml.gdat'), 'rb') as f:
            data = csv.DictReader(f, delimiter =',')

            for row in data:
                for key in row:
                    if key == 'time':
                        continue                        
                    elif key not in [' ']:
                        trajectorydata['Seconds'].append(float(row['time'].strip()))
                        trajectorydata['Value'].append(int(row[key].strip()))
                        trajectorydata['Observable'].append(key.strip())
                        trajectorydata['Origin'].append('R-MCell')
        '''
        trajectorydata = processMDLrData(os.path.join(testname, 'mdlr', 'vol_example.mdlr_total.xml.gdat'))
        localTrajectory = pandas.DataFrame(trajectorydata)

        trajectorydataset = pandas.concat([trajectorydataset, localTrajectory])

    return trajectorydataset

def processMDLrData(fileName, iteration):
    trajectorydata = defaultdict(list)
    trajectorydata['iteration'] = iteration.split('/')[-1]

    with open(fileName, 'rb') as f:
        data = csv.DictReader(f, delimiter =',')

        for row in data:
            for key in row:
                if key == 'time':
                    continue                        
                elif key not in [' ']:
                    trajectorydata['Seconds'].append(float(row['time'].strip()))
                    trajectorydata['Value'].append(int(row[key].strip()))
                    trajectorydata['Observable'].append(key.strip())
                    trajectorydata['Origin'].append('R-MCell')
    return trajectorydata


def compareTimeSeries(mdldataset):
    '''
    performs a kolmogorov-smirnoff comparison
    '''
    keys =  list(set(mdldataset['Observable']))

    keys = [x for x in keys if x  not in ['Seconds','iteration']]
    timepoints = sorted(list(set(mdldataset['Seconds'])))
    for timesampleIdx in range(len(timepoints)/params['segments'], len(timepoints), len(timepoints)/params['segments']):
        #print(timepoints[timesampleIdx])
        mdlslice = mdldataset.query('(Origin == "Standard MCell")').query('(Seconds == {0})'.format(timepoints[timesampleIdx]))
        mdlrslice = mdldataset.query('(Origin == "R-MCell")').query('(Seconds == {0})'.format(timepoints[timesampleIdx]))

        for observable in keys:
            if observable not in ['LynFree']:
                continue

            mdlobs = mdlslice.query('(Observable == "{0}")'.format(observable))['Value']
            mdlrobs= mdlrslice.query('(Observable == "{0}")'.format(observable))['Value']
            if len(mdlobs) == 0 or len(mdlrobs) == 0:
                continue
            kmetric, pvalue = stats.ks_2samp(list(mdlobs), list(mdlrobs))
            sd = 1.22 * ((len(mdlobs)+ len(mdlrobs))*1.0/ (len(mdlobs)*len(mdlrobs))) ** 0.5
            if pvalue < 0.1:
            #if kmetric > sd:
                print bcolors.FAIL
            print timepoints[timesampleIdx],observable
            print(' k-smirnoff test:', kmetric, pvalue, sd)
            print(' stats', np.mean(list(mdlobs)), np.mean(list(mdlrobs)),np.std(list(mdlobs)),np.std(list(mdlrobs)))
            if pvalue < 0.1:
                print bcolors.ENDC
            #if kmetric >    1.22 * ((len(mdlobs)+ len(mdlrobs))*1.0/ (len(mdlobs)*len(mdlrobs))) ** 0.5:
            #    raise Exception
            #    raise Exception

def generateData(params, databasename):

    dataset = MDLTrajectoryGeneration(params)
    dataset.to_hdf('{0}DB.h5'.format(databasename), '{0}'.format(params['testname']))

    dataset = pandas.read_hdf('{0}DB.h5'.format(databasename), '{0}'.format(params['testname']))
    dataset = MDLRTrajectoryGeneration(params, dataset)
    dataset.to_hdf('{0}DB.h5'.format(databasename), '{0}'.format(params['testname']))

def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-t','--test',type=str,help='Test to run')
    return parser    


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()

    params = {}
    params['mcell'] = 'mcell'
    params['testname'] = namespace.test
    params['repetitions'] = 10
    params['segments'] = 50
    databasename = 'timeseries3'

    #generateData(params,databasename)

    mdldataset = pandas.read_hdf('{0}DB.h5'.format(databasename), '{0}'.format(params['testname']))
    #mdlrdataset = pandas.read_hdf('{0}DB.h5'.format(databasename), '{0}_mdlr'.format(params['testname']))

    compareTimeSeries(mdldataset)