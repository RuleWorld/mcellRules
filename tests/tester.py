import unittest
import os
import numpy as np
import subprocess
import re
import fnmatch
import sys
import pandas
import csv
from collections import defaultdict
import progressbar

bngPath = os.path.join('.', 'BioNetGen-2.2.6-stable', 'BNG2.pl')
#bngPath = '/home/proto/workspace/bionetgen/bng2/BNG2.pl'  # <<< SET YOUR BIONETGEN PATH HERE <<<
nfsimPath = os.path.join('..', 'build', 'NFsim')


class ParametrizedTestCase(unittest.TestCase):

    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """

    def __init__(self, methodName='runTest', param=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param

    @staticmethod
    def parametrize(testcase_klass, param=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, param=param))
        return suite


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

# don't raise an exception on division by zero
np.seterr(divide='ignore', invalid='ignore')


class TestScenario(ParametrizedTestCase):
    def MDLTrajectoryGeneration(self):
        mcellbinary = self.param['mcell']
        testname = self.param['testname']
        repetitions = self.param['repetitions']
        trajectorydataset = pandas.DataFrame()
        progress = progressbar.ProgressBar()
        print 'Generating MDL data..'
        for idx in progress(range(repetitions)):

            trajectorydata = defaultdict(list)
            #trajectorydata['origin'] = 'mdl'
            trajectorydata['iteration'] = idx


            with open(os.devnull, "w") as fnull:
                subprocess.check_call([mcellbinary, os.path.join(testname, 'reference', 'vol_example.main.mdl')], stdout=fnull)

            with open('counts.txt', 'rb') as f:
                data = csv.DictReader(f, delimiter = ' ')

                for row in data:
                    for key in row:
                        if key == 'Seconds':
                            trajectorydata[key].append(float(row[key]))
                        else:
                            trajectorydata[key].append(int(row[key]))
            localTrajectory = pandas.DataFrame(trajectorydata)

            trajectorydataset = pandas.concat([trajectorydataset, localTrajectory])
        return trajectorydataset

    def MDLRTrajectoryGeneration(self):
        mcellbinary = self.param['mcell']
        testname = self.param['testname']
        repetitions = self.param['repetitions']
        trajectorydataset = pandas.DataFrame()
        progress = progressbar.ProgressBar()
        print 'Generating MDLr data..'
        for idx in progress(range(repetitions)):

            trajectorydata = defaultdict(list)
            #trajectorydata['origin'] = 'mdlr'
            trajectorydata['iteration'] = idx

            with open(os.devnull, "w") as fnull:
                subprocess.check_call([mcellbinary, os.path.join(testname, 'mdlr', 'vol_example.main.mdl'),
                                       '-n', os.path.join(testname, 'mdlr', 'vol_example.mdlr_total.xml')], stdout=fnull, stderr=fnull)
            with open(os.path.join(testname, 'mdlr', 'vol_example.mdlr_total.xml.gdat'), 'rb') as f:
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

    def compareTimeSeries(self, mdldataset, mdlrdataset):
        '''
        performs a kolmogorov-smirnoff comparison
        '''
        keys =  list(mdldataset)
        keys = [x for x in keys if x  not in ['Seconds','iteration']]

        timepoints = sorted(list(set(mdldataset['Seconds'])))
        for timesampleIdx in range(len(timepoints)/5, len(timepoints), len(timepoints)/5):
            mdlslice = mdldataset.query('(Seconds == {0})'.format(timepoints[timesampleIdx]))
            mdlrslice = mdlrdataset.query('(Seconds == {0})'.format(timepoints[timesampleIdx]))
            for observable in keys:
                mdlobs = mdlslice[observable]
                mdlrobs= mdlrslice[observable]
                alpha, pvalue = stats.ks_2samp(list(mdlobs), list(mdlrobs))
                self.assertTrue(pvalue > 0.1)
                

    def test_scenario(self):
        if self.param['generate_mdl']:
            mdl = self.MDLTrajectoryGeneration()
            mdl.to_hdf('{0}DB.h5'.format('testname'), '{0}_mdl'.format(self.param['testname']))

        if self.param['generate_mdlr']:
            mdlr = self.MDLRTrajectoryGeneration()
            mdlr.to_hdf('{0}DB.h5'.format('testname'), '{0}_mdlr'.format(self.param['testname']))
        
        
        mdldataset = pandas.read_hdf('{0}DB.h5'.format('testname'), '{0}_mdl'.format(self.param['testname']))
        mdlrdataset = pandas.read_hdf('{0}DB.h5'.format('testname'), '{0}_mdlr'.format(self.param['testname']))

        self.compareTimeSeries(mdldataset,mdlrdataset)
        




def getTests(directory):
    """
    Gets a list of bngl files that could be correctly translated in a given 'directory'
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, '*txt'):
            matches.append(''.join(filename.split('.')[0][1:]))
    return sorted(matches)

if __name__ == "__main__":
    suite = unittest.TestSuite()

    tests = next(os.walk('.'))[1]
    #for test in tests:
    suite.addTest(ParametrizedTestCase.parametrize(TestScenario, param={'mcell': 'mcell', 'testname': 'vol_vol', 
                    'repetitions': 50, 'generate_mdl':False,'generate_mdlr':False}))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    #print '++++', result, result.failures, result.errors, list(result.errors) == []
    ret = (list(result.failures) == [] and list(result.errors) == [])
    ret = 0 if ret else 1
    print ret
    sys.exit(ret)
