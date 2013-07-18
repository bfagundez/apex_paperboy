#this scripts freezes mm.py and places it in the dist directory
import sys
import argparse
import shutil
import os
import subprocess
import pipes
sys.path.append('../')
import lib.mm_util as mm_util

mavensmate_path     = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
pyinstaller_path    = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))+"/tools/pyinstaller-dev"
mm_path             = os.path.dirname(os.path.dirname(__file__))
mm_build_path       = os.path.dirname(__file__)
build_settings      = mm_util.parse_json_from_file('build_settings.json')

def main():
    #remove dist directory
    if os.path.exists("{0}/dist".format(mm_path)):
        shutil.rmtree("{0}/dist".format(mm_path))
    
    #remove mm directory from pyinstaller
    if os.path.exists(pyinstaller_path+"/mm"):
        shutil.rmtree(pyinstaller_path+"/mm")

    #run pyinstaller on mm.py
    os.chdir(pyinstaller_path)
    pyinstaller_command = "{0} pyinstaller.py {1} --onedir {2}".format(
        pipes.quote(build_settings['python_location']), 
        pipes.quote(mm_path+"/mm.py"), 
        pipes.quote(mm_path+"/mm.spec"))

    print '>>>> ', pyinstaller_command
    p = subprocess.Popen(pyinstaller_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    if p.stdout is not None : 
        for line in p.stdout.readlines():
            print line
    elif p.stderr is not None :
        print "****ERROR****"
        for line in p.stderr.readlines():
            print line

    #copy frozen mm to mm dist path
    shutil.copytree("{0}/mm/dist".format(pyinstaller_path), "{0}/dist".format(mm_path))
    
    #copy mm bin contents to mm/dist/mm/bin
    shutil.copytree("{0}/bin".format(mm_path), "{0}/dist/mm/bin".format(mm_path))

    #copy mm lib contents to mm/dist/mm/lib
    os.rename("{0}/dist/mm/lib".format(mm_path), "{0}/dist/mm/lib2".format(mm_path))
    shutil.copytree("{0}/lib".format(mm_path), "{0}/dist/mm/lib".format(mm_path))
    shutil.copytree("{0}/dist/mm/lib2/python2.7".format(mm_path), "{0}/dist/mm/lib/python2.7".format(mm_path))
    shutil.rmtree("{0}/dist/mm/lib2".format(mm_path))

    #run install_name_tool on libpython2.7.dylib
    # os.chdir("{0}/dist/mm".format(mm_path))
    # point_to_dylib_command = "/usr/bin/install_name_tool -change /usr/lib/libSystem.B.dylib {0} libpython2.7.dylib".format(
    #     pipes.quote("@loader_path/lib/dyn/libSystem.B.dylib"))

    # print '>>>> ', point_to_dylib_command 
    # p = subprocess.Popen(point_to_dylib_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    # if p.stdout is not None : 
    #     for line in p.stdout.readlines():
    #         print line
    # elif p.stderr is not None :
    #     print "****ERROR****"
    #     for line in p.stderr.readlines():
    #         print line

if  __name__ == '__main__':
    main()