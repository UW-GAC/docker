#! /usr/bin/env python
import     time
import     csv
import     sys
import     os.path
import     os
import     subprocess
from       argparse import ArgumentParser
from       datetime import datetime, timedelta
import     requests
import     boto3

# init globals
version='2.0'
msgErrPrefix='>>> Error (' + os.path.basename(__file__) +') '
msgInfoPrefix='>>> Info (' + os.path.basename(__file__) +') '
debugPrefix='>>> Debug (' + os.path.basename(__file__) +') '

# def aws env
def getAWSEnv():
    baseURL = 'http://169.254.169.254/latest/meta-data/'
    try:
        ami = requests.get(baseURL+'ami-id', timeout=1).text
        it = requests.get(baseURL+'instance-type', timeout=1).text
        ii = requests.get(baseURL+'instance-id', timeout=1).text
        rd = {'ami_id': ami, 'instance_type': it, 'instance_id': ii}
    except:
        rd = {'ami_id': 'n/a', 'instance_type': 'n/a', 'instance_id': 'n/a'}
    return rd

# def logger class
class Logger(object):
    def __init__(self, logfile):
        self.terminal = sys.stdout
        self.log = open(logfile, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        self.log.flush()
        pass

    def __del__(self):
        self.write("\n")    # in case we really append next time
        self.log.close()

# def functions
def flush():
    if trace:
        myLogger.flush()
    else:
        sys.stdout.flush()

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
    print( '\tR driver file: ' + rdriver )
    print( '\tR driver args: ' + rargs)
    if logfile != "":
        print( '\tLog file: ' + fullLog)
        if trace == 1:
            print( '\tTrace file: ' + fullTrace)
    print( '\tSystem parameters:' )
    print( '\t\tWorking directory: ' + workdir )
    if bind == 1:
        print("\t\tNot mounting network storage (should be mounted via docker run -v command)")
    else:
        print( '\t\tMount command: '+ mount )
        print( '\t\tMount timeout: '+ tmo)
    if debug:
        print( '\tDebug: True' )
    else:
        print( '\tDebug: False' )
    if arrayType:
        print( '\tArray type: True' )
        print( '\tArray index: ' + arrayIndex )
        print( '\tFirst index: ' + firstSegIndex)
        print( '\tSGE Task ID: ' +  os.environ['SGE_TASK_ID'])
    else:
        print( '\tArray type: False')
    ae = getAWSEnv()
    print( '\tAWS Instance type: ' + ae['instance_type'] )
    print( '\tAWS Instance id: ' + ae['instance_id'] )
    print( '\tAWS AMI: ' + ae['ami_id'] )
    tbegin=time.asctime()
    print( '\tTime: ' + tbegin + "\n" )


# default names
defaultRdriver = "/usr/local/analysis_pipeline/runRscript.sh"
defaultMount = "mount -t nfs4 -o vers=4.1 172.255.44.97:/ /projects"

# command line parser
parser = ArgumentParser( description = "docker script to run tm analysis pipeline R code via R control file (e.g., runRscript.sh)" )
parser.add_argument( "-w", "--workdir",
                     help = "full path of working directory (where pipeline jobs are submitted)" )
parser.add_argument( "-b", "--bindmount", type = int, default = 1,
                     help = "bind-mount of data volume via -v option in docker run [default: 1]" )
parser.add_argument( "--rdriver", default = defaultRdriver,
                     help = "full path of pipeline R driver bash file [default: " + defaultRdriver + "]" )
parser.add_argument( "-m", "--mountcmd", default = defaultMount,
                     help = "if not bind-mount, mount command of data volume " +
                     "[default command: " + defaultMount + "]" )
parser.add_argument( "--rargs", default = "",
                     help = "R driver arguments" )
parser.add_argument( "-D", "--Debug", type = int, default = 0,
                     help = "Turn on debug output [default: 0]" )
parser.add_argument( "-P", "--printonly", type = int, default = 0,
                     help = "Print summary without executing [default: 0]" )
parser.add_argument( "-l", "--logfile", default = "",
                     help = "log filename" )
parser.add_argument( "-T", "--mounttmo", help = "mount timeout", default = "10.0" )
parser.add_argument( "-a", "--arraytype", type = int, default = 0,
                     help = "Batch job is array type [default: 0]" )
parser.add_argument( "-t", "--tracefile", type = int, default = 1,
                     help = "Enable trace file (if logging) [default: 1]" )
parser.add_argument( "--polltime", type = int, default = 5,
                     help = "Time of subprocess polling loop [default: 5]" )
parser.add_argument( "--version", action="store_true", default = False,
                     help = "Print version of " + __file__ )


args = parser.parse_args()
# set result of arg parse_args
rdriver = args.rdriver
workdir = args.workdir
rargs = args.rargs
mount = args.mountcmd
logfile = args.logfile
tmo = args.mounttmo
bind = args.bindmount
debug = args.Debug
po = args.printonly
mounttmo = args.mounttmo
arrayType = args.arraytype
trace = args.tracefile
polltime = args.polltime
# version
if args.version:
    print(__file__ + " version: " + version)
    sys.exit()

# required workdir
if workdir == None:
    pError("--workdir is required but not specified")
    sys.exit(2)
if not os.path.isdir( workdir ):
    pError( "Work directory " + workdir + " does not exist" )
    sys.exit(2)
# change working directory
os.chdir(workdir)
pInfo( "Changed working directory to " + workdir )

# handle array type
if arrayType:
    # get the batch array index, the first segment index and set SGE_TASK_ID
    # which corresponds to a segment index in a chromosome
    echeck = 'AWS_BATCH_JOB_ARRAY_INDEX'
    if echeck in os.environ:
        arrayIndex = os.environ[echeck]
    else:
        pError("Required array job env " + echeck + " not found")
        sys.exit(2)
    echeck = 'FIRST_INDEX'
    if echeck in os.environ:
        firstSegIndex = os.environ[echeck]
    else:
        pError("Required first index env " + echeck + " not found")
        sys.exit(2)
    taskID = str(int(arrayIndex) + int(firstSegIndex))
    os.environ['SGE_TASK_ID'] = taskID

# check for logile and trace file; if so, make it a full path to working directory
logExt = ".log"

if logfile != "":
    if arrayType:
        fullLog = logfile + "_" + taskID + logExt
    else:
        fullLog = logfile + logExt
    fullLog = workdir + "/" + fullLog
    # trace
    traceExt = ".trace"
    if trace == 1:
        if arrayType:
            fullTrace = logfile + "_" + taskID + traceExt
        else:
            fullTrace = logfile + traceExt
    fullTrace = workdir + "/" + fullTrace
    myLogger = Logger(fullTrace)
    sys.stderr = sys.stdout = myLogger
else:
    trace = 0


# summarize and check for required params
Summary("Summary of " + __file__)

# mount
if bind == 0:
    # check if the mount point (last arg in mount command) exists; if not create it
    if po == 0:
        if not os.path.isdir( mount.split()[-1] ):
            os.mkdir(mount.split()[-1])
    pDebug( "mount tmo: " + tmo + " mount command: " + mount )
    flush()
    mtmo = "timeout " + tmo + " " + mount
    pInfo("Mount command data volume: " + mtmo)
    if po == 0:
        process = subprocess.Popen(mtmo, shell=True, stdout=subprocess.PIPE)
        status = process.wait()
        pipe = process.stdout
        msg = pipe.readline()
        if status == 32:
            pInfo("Warning: mount volume already mounted.")
        elif status:
            if status == 124:
                msg = "mount timed out"
            pError("Mount error: " + msg )
            sys.exit(2)
else:
    pInfo( "Data volume is bind-mounted" )

# check for files and folders exists
if po == 0:
    if not os.path.isfile( rdriver ):
        pError( "R control file " + rdriver + " does not exist" )
        sys.exit(2)
# execute the R control file
cmd = rdriver + ' ' + rargs
pInfo( "Executing " + cmd )
flush()
if po == 0:
    # redirect stdout to logile
    if logfile != "":
        sout = sys.stdout
        serr = sys.stderr
        flog = open ( fullLog, 'w' )
        sys.stderr = sys.stdout = flog
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True)
    status = process.wait()
    # redirect stdout back
    if logfile != "":
        sys.stdout = sout
        sys.stderr = serr
    flush()
    if status:
        pError( "Executing R driver file failed (" + str(status) + ")" )
        sys.exit(2)
    else:
        pInfo( "Executing R driver file completed without errors.")
else:
    pInfo('Print-only completed')
