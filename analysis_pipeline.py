#! /usr/bin/env python
# this script creates a docker container to initiate an analysis pipeline
# run and submit a job to aws batch.
import     time
import     csv
import     sys
import     os.path
import     os
import     subprocess
from       argparse import ArgumentParser
from       datetime import datetime, timedelta

# init globals
version='1.0'
msgErrPrefix='>>> Error (' + os.path.basename(__file__) +')'
msgInfoPrefix='>>> Info (' + os.path.basename(__file__) +')'
debugPrefix='>>> Debug (' + os.path.basename(__file__) +')'

# def functions
def add2parameters(inparams,inopt,inoptVal):
    params=inparams
    # if inopt not already defined add to params
    if inopt not in params:
        params=params + " " + inopt
        if inoptVal is not None:
            params=params + " " + inoptVal
    return params


def pInfo(msg):
    tmsg=time.asctime()
    print msgInfoPrefix+tmsg+": "+msg

def pError(msg):
    tmsg=time.asctime()
    print msgErrPrefix+tmsg+": "+msg

def pDebug(msg):
    if debug:
        tmsg=time.asctime()
        print debugPrefix+tmsg+": "+msg

def Summary(hdr):
    print(hdr)
    print( '\tVersion: ' + version)
    print( '\tWork dir: ' + workdir )
    print( '\tAnalysis: ' + analysis)
    print( '\tLocal security file: ' + localsecurity)
    print( '\tSecurity in docker: ' + dockersecurity)
    print( '\tAnalysis parameters: ' + parameters)
    print( '\tAnalysis pipeline path: ' + pipepath)

    print( '\tDocker:' )
    print( '\t\tUse existing container: ' + str(existingcontainer) )
    print( '\t\tKeep container: ' + str(keepcontainer) )
    print( '\t\tContainer name: ' + name )
    print( '\t\tImage: ' + image )
    print( '\t\tScript: ' + script )
    print( '\t\tCreate container opts: ' + createopts )
    print( '\t\tBind-mount local: ' + plocal )
    print( '\t\tBind-mount container: ' + pdocker )
    tbegin=time.asctime()
    print( '\tTime: ' + tbegin + "\n" )

defCreateOpts = "-it"
defDockerSecurity = "/root/.aws"
defLocalSecurity = "~/.aws/credentials"
defProjectDocker = "/projects"
defDockerImage = "uwgac/topmed-roybranch"
defDockerScript = "docker2aws.py"
defPipeline = "/usr/local/analysis_pipeline"
defName = "ap_batch"

# command line parser
parser = ArgumentParser( description = "Helper function to execute analysis pipeline via docker" )
parser.add_argument( "-w", "--workdir",
                     help = "full path of working directory [default: current working directory]" )
parser.add_argument( "-a", "--analysis",
                     help = "analysis to run (e.g., assoc)" )
parser.add_argument( "-p", "--parameters",
                     help = 'analysis parameters(e.g., "single assoc.cfg --chromosomes 1-4")')
parser.add_argument( "-i", "--image", default = defDockerImage,
                     help = "docker image to initiate pipeline execution [default: " + defDockerImage + "]")
parser.add_argument( "-s", "--script", default = defDockerScript,
                     help = "script in docker image to initiate pipeline execution [default: " + \
                             defDockerScript + "]")
parser.add_argument( "-c", "--createopts", default = defCreateOpts,
                     help = "docker create container options [default: " + defCreateOpts + "]")
parser.add_argument( "--plocal",
                     help = "/projects bind mount in local computer [default: project root from workdir]" )
parser.add_argument( "--pdocker", default = defProjectDocker,
                     help = "/projects bind mount in docker container [default: " + defProjectDocker + "]" )
parser.add_argument( "--pipepath", default = defPipeline,
                     help = "pipeline path in docker image [default: " + defPipeline + "]" )
parser.add_argument( "--localsecurity", default = defLocalSecurity,
                     help = "aws credentials file to copy to docker [default: ]" + defLocalSecurity + "]" )
parser.add_argument( "--dockersecurity", default = defDockerSecurity,
                     help = "security file location in docker [default: " + defDockerSecurity + "]" )
parser.add_argument( "-e","--existingcontainer", action="store_true", default = False,
                     help = "start an existing container [default: False]" )
parser.add_argument( "-n","--name", default = defName,
                     help = "name of container [default: " + defName + "]" )
parser.add_argument( "-k", "--keepcontainer", action="store_true", default = False,
                     help = "Keep the container and do not stop it [default: False]" )
parser.add_argument( "-V", "--verbose", action="store_true", default = False,
                     help = "Turn on verbose output [default: False]" )
parser.add_argument( "-S", "--summary", action="store_true", default = False,
                     help = "Print summary prior to executing [default: False]" )
parser.add_argument( "--version", action="store_true", default = False,
                     help = "Print version of " + __file__ )
parser.add_argument( "-P", "--printonly", action="store_true", default = False,
                     help = "Print summary without executing [default: False]" )
parser.add_argument( "-C","--clustercfg", default = None,
                     help = "name of cluster cfg file in the working directory [default: None]" )

args = parser.parse_args()
# set result of arg parse_args
workdir = args.workdir
analysis = args.analysis
parameters = args.parameters
image = args.image
script = args.script
createopts = args.createopts
plocal = args.plocal
pdocker = args.pdocker
localsecurity = args.localsecurity
dockersecurity = args.dockersecurity
existingcontainer = args.existingcontainer
name = args.name
keepcontainer = args.keepcontainer
verbose = args.verbose
pipepath = args.pipepath
summary = args.summary
printonly = args.printonly
clustercfg = args.clustercfg
# version
if args.version:
    print(__file__ + " version: " + version)
    sys.exit()

if not keepcontainer:
    createopts = createopts + " --rm"
# if not using existing container, then process all the args
if not existingcontainer:
    if parameters == None:
        pError("--parameters is required but not specified")
        sys.exit(2)
    if analysis == None:
        pError("--analysis is required but not specified")
        sys.exit(2)
    # check workdir; if not passed using cwd
    if workdir == None:
        workdir = os.getenv('PWD')
    wl = workdir.split("/")
    workdir_a = "/" + "/".join(wl[wl.index('projects'):len(wl)])

    # handle plocal (local bind mount to projects)
    if plocal == None:
        # find /projects in the workdir and use that root
        dirlist = workdir.split("/")
        plocal = "/".join(dirlist[0:dirlist.index('projects')+1])

    # if printonly, add to parameters
    if printonly:
        parameters =  add2parameters(parameters,"--print_only",None)

    # if clusterconfig file is passed, add to parameters
    if clustercfg is not None:
        parameters = add2parameters(parameters,"--cluster_file",clustercfg)

    # if verbose, add to parameters
    if verbose:
        parameters = add2parameters(parameters,"--verbose",None)
else:
    parameters = "N/A"
    analysis = "N/A"
    workdir = "N/A"
    image = "N/A"
    script = "N/A"
    createopts = "N/A"
    plocal = "N/A"
    pdocker = "N/A"
    localsecurity = "N/A"
    dockersecurity = "N/A"
# summarize and check for required params
if summary or verbose:
    Summary("Summary of " + __file__)
    if summary:
        sys.exit()
print("=====================================================================")
pInfo("\n\tSending analysis to docker image: " + image)
print("=====================================================================")
# create container and copy security
if not existingcontainer:
    dsFile = dockersecurity + "/" + os.path.basename(localsecurity)
    createCMD = "docker create " + createopts + " --name " + name + \
                " -v " + plocal + ":" + pdocker + \
                " " + image + " " + script + " --pipepath " +  pipepath + \
                " -w " + workdir_a  + " -s " + dsFile + \
                " -a " + analysis + " -p '" + parameters + "'"
    if verbose:
        pInfo("Docker create container cmd:\n" + createCMD)
    process = subprocess.Popen(createCMD, shell=True, stdout=subprocess.PIPE)
    status = process.wait()
    pipe = process.stdout
    msg = pipe.readline()
    if status:
        pError("Docker create command failed: " + msg )
        sys.exit(2)

    copyCMD = "docker cp " + localsecurity + " " + name + ":" + dockersecurity
    if verbose:
        pInfo("Docker copy cmd:\n" + copyCMD)
    process = subprocess.Popen(copyCMD, shell=True, stdout=subprocess.PIPE)
    status = process.wait()
    pipe = process.stdout
    msg = pipe.readline()
    if status:
        pError("Docker copy command failed:\n\t" + msg )
        sys.exit(2)
# just use existing container
else:
    if verbose:
        pInfo("Use existing container named: " + name)

# start the container
startCMD = "docker start -i " + name
if verbose:
    pInfo("Docker start cmd: " + startCMD)
process = subprocess.Popen(startCMD, stdout=sys.stdout, stderr=sys.stderr, shell=True)
status = process.wait()
if status:
    pError("Docker start command failed:\n\t" + str(status) )
    sys.exit(2)

if verbose:
    pInfo("Python script " + __file__ + " completed without errors")
