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
    print( '\tLocal work dir: ' + workdir )

    print( '\tDocker:' )
    print( '\t\tUse existing container: ' + str(existingcontainer) )
    print( '\t\tKeep container: ' + str(keepcontainer) )
    print( '\t\tContainer name: ' + name )
    print( '\t\tImage: ' + image )
    print( '\t\tCreate container opts: ' + createopts )
    print( '\t\tBind-mount local: ' + plocal )
    print( '\t\tBind-mount container: ' + pdocker )
    print( '\t\tWorking directory: ' + workdir_a )
    print( '\t\tNumber of threads: ' + threads )

defCreateOpts = "-it"
defDockerImage = "uwgac/topmed-roybranch"
defApath = "/usr/local/analysis_pipeline/R"
defName = "ap_analysis"
defTPVersion = "00.00"
defThreads = "1"

# command line parser
parser = ArgumentParser( description = "Helper function to run a pipeline analysis in docker" )
parser.add_argument( "-w", "--workdir",
                     help = "full path of working directory [default: current working directory]" )
parser.add_argument( "--path", default = defApath,
                     help = "analysis path in docker image [default: " + defApath + "]" )
parser.add_argument( "-a", "--analysis",
                     help = "analysis to run (e.g., assoc_single)" )
parser.add_argument( "-p", "--parameters",
                     help = 'analysis parameters(e.g., "assoc.cfg --chromosome 4 --segment 2")')
parser.add_argument( "-N", "--nothreads", default = defThreads,
                     help = "Number of threads [default: " +defThreads + "]")

parser.add_argument( "-i", "--image", default = defDockerImage,
                     help = "docker image to initiate pipeline execution [default: " + defDockerImage + "]")
parser.add_argument( "-c", "--createopts", default = defCreateOpts,
                     help = "docker create container options [default: " + defCreateOpts + "]")
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

args = parser.parse_args()
# set result of arg parse_args
aPath = args.path
analysis = args.analysis
aParameters = args.parameters
threads=args.nothreads

workdir = args.workdir
image = args.image
createopts = args.createopts
existingcontainer = args.existingcontainer
name = args.name
keepcontainer = args.keepcontainer
verbose = args.verbose
summary = args.summary
# version
if args.version:
    print(__file__ + " version: " + version)
    sys.exit()
# build up the R command to execute
Rcmd = "/bin/sh -c " + '"' + "/usr/local/bin/R " +  "-q --vanilla --args " + \
       aParameters + " < " + \
       aPath + "/" + analysis + ".R" + '"'
# container stuff
if not keepcontainer:
    createopts = createopts + " --rm"
# if not using existing container, then process all the args
if not existingcontainer:
    # check workdir; if not passed using cwd
    if workdir == None:
        workdir = os.getenv('PWD')
    wl = workdir.split("/")
    workdir_a = "/" + "/".join(wl[wl.index('projects'):len(wl)])

    # find /projects in the workdir and use that root
    dirlist = workdir.split("/")
    plocal = "/".join(dirlist[0:dirlist.index('projects')+1])
    pdocker = "/projects"

else:
    workdir = "N/A"
    image = "N/A"
    createopts = "N/A"
    plocal = "N/A"
    pdocker = "N/A"
# summarize and check for required params
if summary or verbose:
    Summary("Summary of " + __file__)
    if summary:
        sys.exit()
print("=====================================================================")
pInfo("\n\tRunning R in docker image: " + image)
print("=====================================================================")
# create container
if not existingcontainer:
    # if threading, set env NSLOTS
    if int(threads) > 1:
        envopts = " -e NSLOTS=" + threads + " "
    else:
        envopts = ""
    createCMD = "docker create " + envopts + createopts + " --name " + name + \
                " -v " + plocal + ":" + pdocker + \
                " -w " + workdir_a + \
                " " + image + " " + Rcmd
    if verbose:
        pInfo("Docker create container cmd:\n" + createCMD)
    process = subprocess.Popen(createCMD, shell=True, stdout=subprocess.PIPE)
    status = process.wait()
    pipe = process.stdout
    msg = pipe.readline()
    if status:
        pError("Docker create command failed: " + msg )
        sys.exit(2)
# just use existing container
else:
    if verbose:
        pInfo("Use existing container named: " + name)

# start the container
startCMD = "docker start -i " + name
if verbose:
    pInfo("Docker start cmd: " + startCMD)
pInfo('>>>Analysis begins ...')
process = subprocess.Popen(startCMD, stdout=sys.stdout, stderr=sys.stderr, shell=True)
status = process.wait()
if status:
    pError("Docker start command failed:\n\t" + str(status) )
    sys.exit(2)
pInfo('>>>Analysis completed successfully')

if verbose:
    pInfo("Python script " + __file__ + " completed without errors")
