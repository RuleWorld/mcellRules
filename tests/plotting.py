import seaborn as sns
import pandas
import matplotlib.pyplot as plt
import numpy as np
import argparse

def qqplot(x, y, **kwargs):
    _, xr = stats.probplot(x, fit=False)
    _, yr = stats.probplot(y, fit=False)
    plt.scatter(xr, yr, **kwargs)


def testPlotSeriesArray(mdldataset, testname):
    subplotdict = {1:[1,1],2:[2,1],3:[2,2],4:[2,2],5:[3,2],6:[3,2],7:[3,3],8:[3,3],9:[3,3]}
    columns = len(set(mdldataset['Observable']))
    sns.set_context("paper", font_scale=2.5)
    sns.set_style("white")
    grid = sns.FacetGrid(mdldataset, col="Observable", col_wrap=subplotdict[columns][1], size=1.5, sharey=False, margin_titles=True)
    #grid.fig.xticks(rotation=40)
    grid.fig.set_size_inches(18.5, 10.5)
    grid.map_dataframe(sns.tsplot, time="Seconds", unit="iteration",
                value="Value", condition="Origin", color="deep", ci=[70]).add_legend()
    grid.set_axis_labels("Seconds", "Species counts")
    grid.fig.subplots_adjust(wspace=.5, hspace=.5)
    #grid.set_xticklabels(grid.get_xticklabels(), rotation=30)
    [plt.setp(ax.get_xticklabels(), rotation=40) for ax in grid.axes.flat]
    #for ax in g.axes.flag:
    #    for labels in ax.get.xticklabels():
    #        label.set_rotation(40)

    grid.fig.savefig('{0}TS.pdf'.format(testname), bbox_inches="tight")
    #plt.show()


def testPlotPDEArray(mdldataset, testname, timepoints=6):
    sns.set_context("paper", font_scale=2)
    sns.set_style("white")

    columns = len(set(mdldataset['Observable']))
    timerows = list(set(mdldataset['Seconds']))
    timerows = sorted(timerows)
    timerows = timerows[len(timerows)/timepoints:len(timerows):len(timerows)/timepoints]
    # select a subset of the data
    mdlslice = mdldataset[mdldataset.Seconds.isin(timerows)]
    grid = sns.FacetGrid(mdlslice, col="Observable", row='Seconds', hue='Origin', margin_titles=True,legend_out=False)
    grid.set(xticks=np.arange(0,35,10), yticks=np.arange(0,0.3,0.1))
    grid.map(sns.kdeplot, "Value")
    grid.add_legend()

    grid.fig.savefig('{0}PDE.pdf'.format(testname), bbox_inches="tight")

    #sns.set_context("paper", font_scale=2.5)
    #sns.set_style("white")





def testPlotSeries(mdldataset, mdlrdataset, testname):
    sns.set_context("paper", font_scale=2.5)
    sns.set_style("white")

    subplotdict = {1:[1,1],2:[2,1],3:[2,2],4:[2,2],5:[3,2],6:[3,2],7:[3,3],8:[3,3],9:[3,3]}
    keys =  set(mdldataset['Observable'])
    
    numparams = len(keys)

    for idx,parameter in enumerate(keys):
        print idx, parameter
        mdlslice = mdldataset.query('(Observable == "{0}")'.format(parameter))
        #mdlrslice = mdlrdataset.query('(Observable == "{0}")'.format(parameter))

        plt.subplot(subplotdict[numparams][0], subplotdict[numparams][1], idx+1)
        sns.tsplot(data=mdlslice, time="Seconds", unit="iteration",condition='Origin',
               value="Value",ci=[95])
        #sns.tsplot(data=mdlrslice, time="Seconds", unit="iteration",
        #       value="Value",color="g",ci=[95])
    plt.savefig('{0}b.pdf'.format(testname), bbox_inches="tight")
    plt.show()
    

def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-t','--test',type=str,help='Test to run')

    return parser    


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()

    test = namespace.test
    database = 'timeseries3'
    totaldataset = pandas.read_hdf('{0}DB.h5'.format(database), '{0}'.format(namespace.test))
    #mdldataset = totaldataset.query('(Origin == "Standard MCell")')
    #mdlrdataset = totaldataset.query('(Origin == "R-MCell")')
    #mdlrdataset = pandas.read_hdf('{0}DB.h5'.format('timeseries'), '{0}_mdlr'.format(test))
    mdldataset = totaldataset
    mdlrdataset = None
    #testPlotSeries(mdldataset,mdlrdataset, test)
    #testPlotSeriesArray(mdldataset,test)
    testPlotPDEArray(mdldataset,test,3)


