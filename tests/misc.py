import pandas
import os
from collections import defaultdict
import csv
import subprocess
import progressbar
import random
from scipy import stats
import numpy as np

def MDLTrajectoryGeneration(params):
    mcellbinary = params['mcell']
    testname = params['testname']
    repetitions = params['repetitions']
    trajectorydataset = pandas.DataFrame()
    progress = progressbar.ProgressBar()
    print('Generating MDL data..')
    for idx in progress(range(repetitions)):

        trajectorydata = defaultdict(list)
        trajectorydata['iteration'] = idx


        with open(os.devnull, "w") as fnull:
            subprocess.check_call([mcellbinary, os.path.join(testname, 'reference', 'vol_example.main.mdl'),
                                   '-seed', str(random.randint(1, 100000))], stdout=fnull)

        with open('counts.txt', 'rb') as f:
            data = csv.DictReader(f, delimiter=' ')

            for row in data:
                for key in row:
                    if key == 'Seconds':
                        trajectorydata[key].append(float(row[key]))
                    else:
                        trajectorydata[key].append(int(row[key]))
        localTrajectory = pandas.DataFrame(trajectorydata)

        trajectorydataset = pandas.concat([trajectorydataset, localTrajectory])
    return trajectorydataset

def MDLRTrajectoryGeneration(params):
    mcellbinary = params['mcell']
    testname = params['testname']
    repetitions = params['repetitions']
    trajectorydataset = pandas.DataFrame()
    progress = progressbar.ProgressBar()
    print('Generating MDLr data..')
    for idx in progress(range(repetitions)):

        trajectorydata = defaultdict(list)
        trajectorydata['iteration'] = idx

        with open(os.devnull, "w") as fnull:
            subprocess.check_call([mcellbinary, os.path.join(testname, 'mdlr', 'simple.main.mdl'),
                                   '-n', os.path.join(testname, 'mdlr', 'example.mdlr_total.xml'),
                                   '-seed', str(random.randint(1, 100000))], stdout=fnull, stderr=fnull)
        with open(os.path.join(testname, 'mdlr', 'example.mdlr_total.xml.gdat'), 'rb') as f:
            data = csv.DictReader(f, delimiter =',')

            for row in data:
                for key in row:
                    if key == 'time':
                        trajectorydata['Seconds'].append(float(row[key].strip()))
                    elif key not in [' ']:
                        trajectorydata[key.strip()].append(int(row[key].strip()))
        localTrajectory = pandas.DataFrame(trajectorydata)

        trajectorydataset = pandas.concat([trajectorydataset, localTrajectory])

    return trajectorydataset


def compareTimeSeries(mdldataset, mdlrdataset):
    '''
    performs a kolmogorov-smirnoff comparison
    '''
    keys =  list(mdldataset)
    keys = [x for x in keys if x  not in ['Seconds','iteration']]

    timepoints = sorted(list(set(mdldataset['Seconds'])))
    for timesampleIdx in range(len(timepoints)/params['segments'], len(timepoints), len(timepoints)/params['segments']):
        print timepoints[timesampleIdx]
        mdlslice = mdldataset.query('(Seconds == {0})'.format(timepoints[timesampleIdx]))
        mdlrslice = mdlrdataset.query('(Seconds == {0})'.format(timepoints[timesampleIdx]))
        for observable in keys:
            print(observable)
            mdlobs = mdlslice[observable]
            mdlrobs= mdlrslice[observable]
            _, pvalue = stats.ks_2samp(list(mdlobs), list(mdlrobs))

            print('\t', 'k-smirnoff test:', stats.ks_2samp(list(mdlobs), list(mdlrobs)))
            print('\t', 'stats', np.mean(list(mdlobs)), np.mean(list(mdlrobs)),np.std(list(mdlobs)),np.std(list(mdlrobs)))
            #if pvalue < 0.1:
            #    raise Exception

def generateData(params):

    dataset = MDLTrajectoryGeneration(params)
    dataset.to_hdf('{0}DB.h5'.format('timeseries'), '{0}_mdl'.format(params['testname']))

    dataset2 = MDLRTrajectoryGeneration(params)
    dataset2.to_hdf('{0}DB.h5'.format('timeseries'), '{0}_mdlr'.format(params['testname']))



if __name__ == "__main__":
    params = {}
    params['mcell'] = 'mcell'
    params['testname'] = 'vol_vol'
    params['repetitions'] = 20
    params['segments'] = 5

    generateData(params)

    mdldataset = pandas.read_hdf('{0}DB.h5'.format('timeseries'), '{0}_mdl'.format(params['testname']))
    mdlrdataset = pandas.read_hdf('{0}DB.h5'.format('timeseries'), '{0}_mdlr'.format(params['testname']))

    compareTimeSeries(mdldataset,mdlrdataset)