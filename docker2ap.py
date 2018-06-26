#!/usr/bin/python
import     time
import     csv
import     sys
import     os.path
import     os
import     subprocess
from       argparse import ArgumentParser
from       datetime import datetime, timedelta
from       shutil import copyfile


# init globals
version='1.0'
msgErrPrefix='>>> Error (' + os.path.basename(__file__) +') '
msgInfoPrefix='>>> Info (' + os.path.basename(__file__) +') '
debugPrefix='>>> Debug (' + os.path.basename(__file__) +') '

# def functions
def pInfo(msg):
    print msgInfoPrefix+msg

def pError(msg):
    print msgErrPrefix+msg

def Summary(hdr):
    pInfo(hdr)
    pInfo( '\tVersion: ' + version)
    pInfo( '\tWork directory: ' + workDir )
    pInfo( '\tPipeline analysis:' + analysis)
    pInfo( '\tPipeline analysis parameters:' + parameters)
    pInfo( '\tPipeline path:' + pipepath)
    tbegin=time.asctime()
    pInfo( '\tTime: ' + tbegin + "\n" )


# default names
defaultPP = '/usr/local/analysis_pipeline'
defaultSecFile = '/root/.aws/credentials'

# command line parser
parser = ArgumentParser( description = "run the analysis pipeline (e.g. assoc) by executing a python script which submits jobs to aws batch" )
parser.add_argument( "-w", "--workdir",
                     help = "full path of working directory (where pipeline's analysis is executed)" )
parser.add_argument("-a","--analysis",
                     help = "pipeline analysis (e.g., assoc)" )
parser.add_argument("-p","--parameters",
                     help = "pipeline analysis parameters" )
parser.add_argument( "--pipepath", default = defaultPP,
                     help = "Pipeline path [default: " + defaultPP + "]" )
parser.add_argument( "-s", "--secfile", default = defaultSecFile,
                     help = "aws security file to check [default: " + defaultSecFile + "]" )
parser.add_argument("--version", action="store_true", default = False,
                    help = "Print version of " + __file__ )


args = parser.parse_args()
# set result of arg parse_args
workDir = args.workdir
analysis = args.analysis
parameters = args.parameters
pipepath = args.pipepath
secfile = args.secfile
# version
if args.version:
    print(__file__ + " version: " + version)
    sys.exit()
# check for required args
if workDir is None:
    pError("Working directory (--workdir) must be specified")
    sys.exit(2)
if analysis is None:
    pError("Pipeline analysis (--analysis) must be specified")
    sys.exit(2)
if parameters is None:
    pError("Pipeline analysis parameters (--parameters) must be specified")
    sys.exit(2)

# summarize and check for required params
Summary("======== Summary of " + __file__ + " =================")

# check for files and folders exists
if not os.path.isdir( workDir ):
    pError( "Work directory " + workDir + " does not exist" )
    sys.exit(2)

if not os.path.isfile( secfile ):
    pError( "Security file  " + secfile + " does not exist" )
    sys.exit(2)
# change working directory
pInfo( "CD to " + workDir )
os.chdir(workDir)

# add --cluster_type AWS_Batch if not there
pl = parameters.split()
ct = "--cluster_type"
ab = "AWS_Batch"
if ct not in pl:
    pl.append(ct)
    pl.append(ab)
parameters = ' '.join(pl)

# execute the pipeline command
cmd = 'python ' + pipepath + '/' + analysis + '.py' + ' ' + parameters
pInfo( "Executing " + cmd )
pInfo("==============================================================\n\n")
sys.stdout.flush()
# redirect stdout to logile
process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True)
status = process.wait()
# redirect stdout back
if status:
    pError( "\n\nExecuting pipeline command failed (" + str(status) + ")" )
    sys.exit(2)
else:
    pInfo( "\n\nExecuting pipeline command completed without errors.")
