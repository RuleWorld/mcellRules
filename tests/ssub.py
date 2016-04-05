#!/usr/bin/python
# Example PBS cluster job submission in Python

from popen2 import popen2
import argparse
# If you want to be emailed by the system, include these in job_string:
# PBS -M your_email@address
# PBS -m abe  # (a = abort, b = begin, e = end)

# Loop over your jobs

def start_queue(test, repetitions, threads):


    job_string = """#!/bin/csh
        #!/bin/csh
        #SBATCH -N 1
        #SBATCH -p RM
        #SBATCH -t 48:00:00
        #SBATCH --array=1-{0}
        #SBATCH --job-name=mcnf-volsurf

        #SBATCH --mail-type=ALL
        #SBATCH --mail-user=jjtapia@gmail.com

        set echo

        cd /pylon2/bi4s88p/tapiava/workspace/mcellRules/tests
        python analyzeModelSet.py -t {1} -r {2} -w /pylon1/bi4s88p/tapiava
        python mergeDataFrame.py -w /pylon1/bi4s88p/tapiava/{1}/partial -o {1}.h5
    
    """.format(str(repetitions/threads), test, str(threads))

    print job_string
    output, input = popen2('sbatch')


    # Send job_string to qsub
    input.write(job_string)
    input.close()

    # Print your job and the system response to the screen as it's submitted
    # print(output.read())



def defineConsole():
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-t','--test',type=str, required=True)
    parser.add_argument('-r','--repetitions',type=int,required=True)
    parser.add_argument('-d','--threads',type=int,default=26)

    return parser


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()


    # print len(finalfiles)

    start_queue(namespace.test, namespace.repetitions,namespace.threads)
