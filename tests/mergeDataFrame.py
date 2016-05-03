import argparse
import fnmatch
import os
import pandas
import concurrent.futures
import progressbar
import multiprocessing as mp


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
def dummy(options):
    pass


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
    parser.add_argument('-w','--workDirectory',type=str, help='the folder where the output files will be placed', default=os.getcwd())
    parser.add_argument('-o','--outputfile', type=str)
    return parser    

def mergedataframe(datafilenames, outputdir, index):
    outputfile = os.path.join(outputdir,'merged', index,'.h5')
    trajectorydataset = pandas.DataFrame()
    for df in pandalist:
        tmp = pandas.read_hdf(df)
        trajectorydataset = pandas.concat([trajectorydataset, tmp])
    trajectorydataset.to_hdf(outputfile)


def distributedMerging(datafilenames, outputdir, workers):
    workers = mp.cpu_count() - 1
    progress = progressbar.ProgressBar(maxval=options['repetitions']).start()
    i = 0
    print 'running in {0} cores'.format(workers)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        workunit = min(len(datafilenames)/workers, 2)
        for i in range(0, len(datafilenames), workunit):
            futures.append(executor.submit(mergedataframe, datafilenames[i:i+workunit], outputdir, i))


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    pandalist = getFiles(namespace.workDirectory, 'h5')
    pandasArray = []
    trajectorydataset = pandas.DataFrame()
    workers = mp.cpu_count() - 1

    #distributedMerging(pandalist, 'merged', workers)
    progress = progressbar.ProgressBar()
    options = ['']
    trajectorydataset = pandas.concat([pandas.read_hdf(df) for df in pandalist], ignore_index=True)

    #for dfindex in progress(range(0,len(pandalist))):
    #    df = pandalist[dfindex]
    #    tmp = pandas.read_hdf(df)
    #    trajectorydataset = pandas.concat([trajectorydataset, tmp],ignore_index=True)

    trajectorydataset.to_hdf(namespace.outputfile, 'results')
    
