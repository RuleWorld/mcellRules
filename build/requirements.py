import subprocess
import os
def nfsim():
    subprocess.call(['git', 'clone', 'https://github.com/RuleWorld/nfsim.git'])
    os.chdir('nfsim')
    subprocess.call(['git', 'checkout', 'nfsim_lib_shared_ptr'])
    try:
        os.mkdir('lib')
    except OSError:
        pass
    os.chdir('lib')
    subprocess.call(['cmake', '..'])
    subprocess.call(['make'])
    os.chdir('..')
    os.chdir('..')

def nfsim_lib():
    subprocess.call(['git', 'clone', 'https://github.com/jjtapia/nfsimCInterface'])
    os.chdir('nfsimCInterface')

    try:
        os.mkdir('lib')
    except OSError:
        pass

    os.chdir('lib')
    subprocess.call(['ln','-s',os.path.join('..','..','nfsim','lib','libNFsim.so')])
    os.chdir('..')

    subprocess.call(['ln','-s',os.path.join('..','nfsim','include')])


    try:
        os.mkdir('build')
    except OSError:
        pass
    os.chdir('build')
    subprocess.call(['cmake', '..'])
    subprocess.call(['make'])
    os.chdir('..')
    os.chdir('..')

def mcell():
    subprocess.call(['git', 'clone', 'https://github.com/mcellteam/mcell.git'])
    os.chdir('mcell')
    subprocess.call(['git','checkout','nfsim_diffusion'])
    try:
        os.mkdir('lib')
    except OSError:
        pass

    os.chdir('lib')
    subprocess.call(['ln','-s',os.path.join('..','..','nfsim','lib','libNFsim.so')])
    subprocess.call(['ln','-s',os.path.join('..','..','nfsimCInterface','build','libnfsim_c.so')])
    os.chdir('..')
    try:
        os.mkdir('include')
    except OSError:
        pass
    os.chdir('include')
    subprocess.call(['ln','-s',os.path.join('..','..','nfsimCInterface','src','nfsim_c_structs.h')])
    subprocess.call(['ln','-s',os.path.join('..','..','nfsimCInterface','src','nfsim_c.h')])

    os.chdir('..')
    try:
        os.mkdir('build')
    except OSError:
        pass
    os.chdir('build')
    subprocess.call(['cmake', '..'])
    subprocess.call(['make'])



if __name__ == "__main__":
    nfsim()
    nfsim_lib()
    mcell()