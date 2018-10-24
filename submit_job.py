#! /usr/bin/env python
# submit a single analysis from the analysis pipeline (e.g., ld_loading)
import      os
import      getpass
import      time
import      json
import      math
import      collections
import      sys
from        copy   import deepcopy
from        argparse import ArgumentParser
from        datetime import datetime, timedelta

try:
    import boto3
except ImportError:
    print ("AWS batch not supported.")

# init globals
fileversion='1.0'
msgErrPrefix='>>> Error: '
msgInfoPrefix='>>> Info: '
debugPrefix='>>> Debug: '

# cluster configuration is read from json into nested dictionaries
# regular dictionary update loses default values below the first level
# https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
def updatecfg(d, u):
    ld = deepcopy(d)
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            if len(v) == 0:
                ld[k] = u[k]
            else:
                r = updatecfg(d.get(k, {}), v)
                ld[k] = r
        else:
            ld[k] = u[k]
    return ld

def memoryLimit(job_name, clusterCfg):
    memlim = None
    memLimits = clusterCfg["memory_limits"]
    if memLimits is None:
        return memlim
    jobMem = [ v for k,v in memLimits.iteritems() if job_name.find(k) != -1 ]
    if len(jobMem):
        # just find the first match to job_name
        memlim = jobMem[0]
    return memlim

def getClusterCfg(a_stdcfg, a_optcfg, a_cfgversion):
    # get the standard cluster cfg
    with open(a_stdcfg) as cfgFileHandle:
        clustercfg= json.load(cfgFileHandle)
    # check version
    key = "version"
    if key in clustercfg:
        if clustercfg[key] != a_cfgversion:
            print( "Error: version of : " + a_stdcfg + " should be " + a_cfgversion +
                   " not " + clustercfg[key])
            sys.exit(2)
    else:
        print( "Error: version missing in " + a_stdcfg )
        sys.exit(2)
    key = "debug"
    debugCfg = False
    if key in clustercfg:
        if clustercfg[key] == 1:
            debugCfg = True
    clusterconfig = clustercfg["configuration"]
    if debugCfg:
        pDebug("Dump of " + clustercfg["name"] + " ... \n")
        print json.dumps(clusterconfig, indent=3, sort_keys=True)
    if a_optcfg != None:
        pDebug("Option cluster cfg file: " + a_optcfg)

        with open(a_optcfg) as cfgFileHandle:
            optcfg = json.load(cfgFileHandle)
        key = "version"
        if key in optcfg:
            if optcfg[key] != a_cfgversion:
                print( "Error: version of : " + optCfgFile + " should be " + a_cfgversion +
                       " not " + optcfg[key])
                sys.exit(2)
        optconfiguration = optcfg["configuration"]
        if debugCfg:
            pDebug("Dump of " + optcfg["name"] + " ... \n")
            print json.dumps(optconfiguration, indent=3, sort_keys=True)
        # update
        clusterconfig = updatecfg(clusterconfig, optconfiguration)
        if debugCfg:
            pDebug("Dump of updated cluster cfg ... \n")
            print json.dumps(clusterconfig, indent=3, sort_keys=True)
    return clusterconfig

def submitjob(a_submitParams):
    # get the batch client
    batchC = a_submitParams["batchclient"]
    # get the job parameters
    jobParams = a_submitParams["clustercfg"]["job_parameters"]
    # get the submit options
    submitOpts = a_submitParams["clustercfg"]["submit_opts"]
    # get the run cmd options
    runCmdOpts = a_submitParams["clustercfg"]["run_cmd"]
    # get the queue and pipelinepath
    queue = a_submitParams["clustercfg"]["queue"]
    retryStrategy = a_submitParams["clustercfg"]["retryStrategy"]
    pipelinePath = a_submitParams["apath"]
    array_range = a_submitParams["array_range"]
    # check if array job and > 1 task
    arrayJob = False
    if array_range is not None:
        air = [ int(i) for i in array_range.split( '-' ) ]
        taskList = range( air[0], air[len(air)-1]+1 )
        noJobs = len(taskList)
        if noJobs > 1:
            arrayJob = True
            envName = "FIRST_INDEX"
        else:
            envName = "SGE_TASK_ID"
        # set env variable appropriately
        key = "env"
        if key in submitOpts:
            submitOpts["env"].append( { "name": envName,
                                        "value": str(taskList[0]) } )
        else:
            submitOpts["env"] = [ { "name": envName,
                                    "value": str(taskList[0]) } ]
    # using time set a job id (which is for tracking; not the batch job id)
    job_name = a_submitParams["analysis"]
    trackID = job_name + "_" + str(int(time.time()*100))

    # set the R driver and arguments (e.g., -s rcode cfg --chr cn)
    key = "rd"
    jobParams[key] = os.path.join(pipelinePath, "runRscript.sh")

    key = "ra"
    jobParams[key] = a_submitParams["analysisfile"] + " " + a_submitParams["params"]

    # set the work dir
    key = "wd"
    jobParams[key] = a_submitParams["workdir"]

    # check for number of cores - sge can be 1-8; or 4; etc.  In batch we'll
    # use the highest number.  e.g., if 1-8, then we'll use 8.  in AWS, vcpus
    # is the number of physical + hyper-threaded cores.  to max performance
    # (at an increase cost) allocate 2 vcpus for each core.
    key = "vcpus"
    request_cores = a_submitParams["nocores"]
    submitOpts[key] = request_cores
    key2 = "env"
    if key2 in submitOpts:
        submitOpts[key2].append( { "name": "NSLOTS",
                                   "value": str(request_cores) } )
    else:
        submitOpts[key2]=[ { "name": "NSLOTS",
                             "value": str(request_cores) } ]

    # get memory limit option
    if a_submitParams["maxmem"] != None:
        submitOpts["memory"] = a_submitParams["maxmem"]
    else:
        memlim = memoryLimit(job_name, a_submitParams["clustercfg"])
        if memlim != None:
            submitOpts["memory"] = memlim

    # holdid is a previous submit_id dict {job_name: [job_Ids]}
    submitHolds = []

    # environment variables
    key = "env"
    if key in submitOpts:
        submitOpts[key].append( { "name": "JOB_ID",
                                  "value": trackID } )
    else:
        submitOpts[key]=[ { "name": "JOB_ID",
                            "value": trackID } ]

    # if we're doing an array job, specify arrayProperty; else just submit one job
    print_only = a_submitParams["test"]
    # array job or single job
    if arrayJob:
        subName = job_name + "_" + str(noJobs)
        jobParams["at"] = "1"
        jobParams['lf'] = trackID + ".task"
        pDebug("\t1> submitJob: " + subName + " is an array job")
        pDebug("\t1>\tNo. tasks: " + str(noJobs))
        pDebug("\t1>\tFIRST_INDEX: " + str(taskList[0]))
        if not print_only:
            try:
                subOut = batchC.submit_job(
                               jobName = subName,
                               jobQueue = queue,
                               arrayProperties = { "size": noJobs },
                               jobDefinition = submitOpts["jobdef"],
                               parameters = jobParams,
                               dependsOn = submitOpts["dependsOn"],
                               containerOverrides = {
                                  "vcpus": submitOpts["vcpus"],
                                  "memory": submitOpts["memory"],
                                  "environment": submitOpts["env"]
                               },
                               retryStrategy = retryStrategy
                )
            except Exception as e:
                pError('boto3 session or client exception ' + str(e))
                sys.exit(2)
    else:
        jobParams["at"] = "0"
        jobParams['lf'] = trackID
        subName = job_name
        pDebug("\t1> submitJob: " + subName + " is a single job")
        if array_range is not None:
            pDebug("\t1> SGE_TASK_ID: " + str(taskList[0]))
        if not print_only:
            try:
                subOut = batchC.submit_job(
                               jobName = subName,
                               jobQueue = queue,
                               jobDefinition = submitOpts["jobdef"],
                               parameters = jobParams,
                               dependsOn = submitOpts["dependsOn"],
                               containerOverrides = {
                                  "vcpus": submitOpts["vcpus"],
                                  "memory": submitOpts["memory"],
                                  "environment": submitOpts["env"]
                               },
                               retryStrategy = retryStrategy
                )
            except Exception as e:
                pError('boto3 session or client exception ' + str(e))
                sys.exit(2)
    if print_only:
        print("+++++++++  Test Only +++++++++++")
        print("Job: " + job_name)
        print("\tSubmit job: " + subName)
        if arrayJob:
            print("\tsubmitJob: " + subName + " is an array job")
            print("\t\tNo. tasks: " + str(noJobs))
            print("\t\tFIRST_INDEX: " + str(taskList[0]))
        elif array_range is not None:
            print("\tsubmitJob: " + subName + " is like array job but with 1 task: ")
            print("\t\tSGE_TASK_ID: " + str(taskList[0]))
        else:
            print("\tsubmitJob: " + subName + " is a single job")
        print("\tlog file: " + jobParams['lf'])
        print("\tJOB_ID: " + trackID)
        print("\tbatch queue: " + queue)
        print("\tjob definition: " + submitOpts["jobdef"])
        print("\tjob memory: " + str(submitOpts["memory"]))
        print("\tjob vcpus: " + str(submitOpts["vcpus"]))
        print("\tjob env: \n\t\t" + str(submitOpts["env"]))
        print("\tjob params: \n\t\t" + str(jobParams))
        jobid = "111-222-333-print_only-" +  subName
        subOut = {'jobName': subName, 'jobId': jobid}
        submit_id = {job_name: [jobid]}
        print("\tsubmit_id: " + str(submit_id))

    # return the "submit_id" which is a list of dictionaries
    submit_id = {job_name: [subOut['jobId']]}
    # return the job id (either from the single job or array job)
    pDebug("\t1> submitJob: " + job_name + " returning submit_id: " + str(submit_id))

    return submit_id

def pInfo(msg):
    tmsg=time.asctime()
    print(msgInfoPrefix+tmsg+": "+msg)

def pError(msg):
    tmsg=time.asctime()
    print(msgErrPrefix+tmsg+": "+msg)

def pDebug(msg):
    if verbose:
        tmsg=time.asctime()
        print(debugPrefix+tmsg+": "+msg)
def Summary(hdr):
    print(hdr)
    print('\tVersion: ' + fileversion)
    print('\tWorking dir: ' + workdir)

    print('\tAnalysis:')
    print('\t\tR file: ' + analysis)
    print('\t\tPath to analysis: ' + apath)
    print('\t\tParameters: ' + workdir)
    print('\t\tArray range: ' + str(arrayrange))
    print('\t\tNo. of cores: ' + str(nocores))
    if maxmem != None:
        print('\t\tMax memory: ' + str(maxmem))
    else:
        print('\t\tMax memory: specifed in cfg file')
    if profile != None:
        print('\t\tAWS profile: ' + profile)
    else:
        print('\t\tAWS profile: specified in cfg file')

    print('\tVerbose: ' + str(verbose))
    tbegin=time.asctime()
    print('\tTime: ' + tbegin + "\n")

defNocores = 1
defApath = "/usr/local/analysis_pipeline"

# command line parser
parser = ArgumentParser(description = "Helper function to submit a batch to run an analysis from analysis pipeline")
parser.add_argument("-w", "--workdir",
                     help = "working directory (full path) [default: current working directory]")

parser.add_argument("-a", "--analysis",
                     help = "analysis to run (e.g., assoc_single)")
parser.add_argument("-p", "--parameters",
                     help = 'analysis parameters(e.g., "assoc.cfg --chromosome 4 --segment 2")')
parser.add_argument("--apath", default = defApath,
                     help = "analysis pipeline path [default: " + defApath + "]")

parser.add_argument("-c", "--cfgfile",
                     help = "custom batch config file [default: None]")
parser.add_argument("--arrayrange",
                     help = "job array range (e.g., 1-22) [default: None]")
parser.add_argument("-N", "--nocores", default = defNocores,
                     help = "Number of cores [default: " + str(defNocores) + "]")
parser.add_argument("-M", "--maxmem",
                     help = "Maximum memory (MB) [default: specified in config file]")
parser.add_argument("-P", "--profile",
                     help = "AWS profile [default: specified in batch config file]")

parser.add_argument("-V", "--verbose", action="store_true", default = False,
                     help = "Turn on verbose output [default: False]")
parser.add_argument("-S", "--summary", action="store_true", default = False,
                     help = "Print summary prior to executing [default: False]")
parser.add_argument("-T", "--test", action="store_true", default = False,
                     help = "Test without executing [default: False]")
parser.add_argument("--version", action="store_true", default = False,
                     help = "Print version of " + __file__)

args = parser.parse_args()
analysis = args.analysis
parameters = args.parameters
workdir = args.workdir
apath = args.apath
cfgfile = args.cfgfile
nocores = int(args.nocores)
maxmem = int(args.maxmem)
profile = args.profile
verbose = args.verbose
summary = args.summary
test = args.test
arrayrange = args.arrayrange
version = args.version

if version:
    print(__file__ + " version: " + fileversion)
    sys.exit()

# check path and analysis R file
if not os.path.isdir(apath):
    pError("Analysis pipeline directory " + apath + " does not exist")
    sys.exit(2)
else:
    analysisfile = apath + "/R/" + analysis + ".R"
if not os.path.isfile(analysisfile):
    pError("Analysis " + analysisfile + " does not exist")
    sys.exit(2)

if workdir == None:
    workdir = os.getenv('PWD')
if not os.path.isdir(workdir):
    pError("Work directory " + workdir + " does not exist")
    sys.exit(2)

if cfgfile != None:
    if not os.path.isfile(cfgfile):
        pError("Cluster config file " + cfgfile + " does not exist")
        sys.exit(2)

if summary:
    Summary("Summary of " + __file__)
# get the cluster configuration
pInfo("Getting cluster configuration ...")
cfgversion = "3.1"
stdcfgfile = apath + "/aws_batch_cfg.json"
clustercfg = getClusterCfg(stdcfgfile, cfgfile, cfgversion)

# create the batch client
pInfo("Creating the batch client ...")
try:
    session = boto3.Session(profile_name = clustercfg["aws_profile"])
    batchClient = session.client('batch')
except Exception as e:
    pError('boto3 session or client exception ' + str(e))
    sys.exit(2)

# submit (with test flag to not really submit)
subParams = {
                'batchclient': batchClient,
                'clustercfg': clustercfg,
                'apath': apath,
                'analysis': analysis,
                'analysisfile': analysisfile,
                'params': parameters,
                'array_range': arrayrange,
                'nocores': nocores,
                'maxmem': maxmem,
                'test': test,
                'workdir': workdir
            }
jobid = submitjob(subParams)
if not test:
    pInfo('Job ' + str(jobid) + ' submitted.')
else:
    pInfo('Test job id: ' + str(jobid))
