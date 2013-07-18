#this scripts freezes mm.py and places it in the dist directory
import sys
import argparse
import shutil
import os
import subprocess
import pipes

# path variables
mavensmate_path     = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, os.pardir))
pyinstaller_path    = mavensmate_path+"/tools/pyinstaller-dev"
mm_path             = mavensmate_path+"/mm"
mm_build_path       = mm_path+"/build"

# add mm directory and import lib.mm_util
sys.path.append(mavensmate_path+"/mm")
import lib.mm_util as mm_util

build_settings      = mm_util.parse_json_from_file(mm_build_path+'/build_settings.json')

def main():
    #remove dist directory
    if os.path.exists("{0}/dist".format(mm_path)):
        shutil.rmtree("{0}/dist".format(mm_path))
    
    #remove mm directory from pyinstaller
    if os.path.exists(pyinstaller_path+"/mm"):
        shutil.rmtree(pyinstaller_path+"/mm")

    #get the build settings, or if it doesn't exist use which to find python
    if "python_location" in build_settings and os.path.exists(build_settings["python_location"]):
        python_location = build_settings["python_location"]
    else:
        cmd = "which python"
        p = subprocess.Popen(cmd , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        python_location = out.rstrip()

    #run pyinstaller on mm.py
    os.chdir(pyinstaller_path)
    pyinstaller_command = "{0} pyinstaller.py {1} --onedir {2}".format(
        pipes.quote(python_location), 
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

    #remove files
    shutil.rmtree("{0}/mm".format(pyinstaller_path))

if  __name__ == '__main__':
    main()