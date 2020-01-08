#! /usr/bin/env python3
from __future__ import division
import os
import sys
import time
from   datetime import datetime

from   argparse import ArgumentParser

try:
    import boto3
except ImportError:
    print ("AWS boto3 not installed.")
    sys.exit(2)

def createtaskids(jid, noTasks):
    delim = ":"
    tids = []
    for i in range(noTasks):
        tid = jid + ":" + str(i)
        tids.append(tid)

    return tids

def arraystat(batchC, job, verbose):
    tstats = []
    # get the number of tasks
    key = "arrayProperties"
    jid = job["jobId"]
    noTasks = job[key]["size"]
    if verbose:
        print('Debug arraystat - jid: ' + jid)
        print('Debug arraystat - no. tasks: ' + str(noTasks))
    # build a list of task ids
    tids = createtaskids(jid, noTasks)
    if verbose:
        print("Debug arraystat - task ids: " + str(tids))
    try:
        dj = batchC.describe_jobs(jobs = tids)
    except Exception as e:
        print('describe_jobs exception for array tasks ' + str(e))
        sys.exit(2)
    # get the stats
    jobs = dj['jobs']
    for job in jobs:
        tstat = {}
        tstat['jobName'] = job['jobName']
        tstat['status'] = job['status']
        tstat['index'] = job["arrayProperties"]["index"]
        tstat['jobId'] = job['jobId']
        tstats.append(tstat)

    return tstats

def proc_jobids(batchC, jobids, terminate=False, verbose=False):
    jobstats= []
    arrayinfo = []
    results = [jobinfo, arrayinfo]
    # get the job status
    try:
        jinfo = batchC.describe_jobs(jobs = jobids)
    except Exception as e:
        print('describe_jobs exception ' + str(e))
        sys.exit(2)
    # if found, get info
    noJobs = len(jinfo["jobs"])
    if verbose:
        print("Debug proc_jobids - no. of jobs found: " + str(noJobs))
    if noJobs > 0:
        jobs = jinfo["jobs"]
        for job in jobs:
            if terminate:
                jobid = job['jobId']
                jobdel(batchC, jobid, True, verbose)
                continue;
            jd = {}
            if verbose:
                print("proc_jobids - job info: \n")
                print("\t" + str(job))
            jobtype = "single"
            jobstatus = job['status']
            if "arrayProperties" in list(job.keys()):
                jobtype = "array"
                # for an array job, see if any of the tasks are running
                tstats = arraystat(batchC, job, verbose)
                trun = [ d['jobId'] for d in tstats if d['status'] == 'RUNNING' ]
                if len(trun) > 0:
                    jobstatus = 'RUNNING'
            jobindex = "1"
            dl = ":"
            jd = job['jobName'] + dl + \
                 job['jobId'] + dl + \
                 jobtype + dl + \
                 jobindex + dl + \
                 jobstatus
            jobstats.append(jd)

    results = jobstats
    return results

def taskstat(batchC, jobid, noTasks, verbose):
    taskinfo = []
    # get info on all tasks (<jobid>:<index>)
    for task in range(noTasks):
        tinfo = {}
        tid = jobid + ":" + str(task)
        if verbose:
            print("Debug taskstat - array job id: " + tid)
        try:
            jinfo = batchC.describe_jobs(jobs = [ tid ])
        except Exception as e:
            print('describe_jobs exception for array job ' + str(e))
            sys.exit(2)
        if len(jinfo["jobs"]) > 0:
            theJob = jinfo["jobs"][0]
            if verbose:
                print("job info: \n")
                print(str(theJob))
            index = str(theJob["arrayProperties"]["index"])
            startTime = "N/A"
            stopTime = "N/A"
            tfmt = "%A, %B %d, %Y %I:%M:%S %p"
            key = "startedAt"
            if key in list(theJob.keys()):
                tTime = theJob[key]
                startTime = datetime.fromtimestamp((tTime/1000)).strftime(tfmt)
            key = "stoppedAt"
            if key in list(theJob.keys()):
                tTime = theJob[key]
                stopTime = datetime.fromtimestamp((tTime/1000)).strftime(tfmt)
            tinfo["a. task_id"] = tid
            tinfo["b. \tstart time"] = startTime
            tinfo["c. \tend time"] = stopTime
            tinfo["d. \tindex"] = index
            statusreason = "N/A"
            key = "statusReason"
            if key in list(theJob["container"].keys()):
                statusreason = theJob["container"][key]
            tinfo["e. \tstatus"] = statusreason
            statusinfo = "N/A"
            key = "reason"
            if key in list(theJob["container"].keys()):
                statusinfo = theJob["container"][key]
            tinfo["f. \tstatus info"] = statusinfo
            taskinfo.append(tinfo)
    return taskinfo

def jobstat(batchC, jobid, arrayProperties, verbose):
    jobinfo = {}
    arrayinfo = []
    results = [jobinfo, arrayinfo]
    # get the job status
    try:
        jinfo = batchC.describe_jobs(jobs = [ jobid ])
    except Exception as e:
        print('describe_jobs exception ' + str(e))
        sys.exit(2)
    # if found, get info
    if len(jinfo["jobs"]) > 0:
        theJob = jinfo["jobs"][0]
        if verbose:
            print("jobstat - job info: \n")
            print("\t" + str(theJob))
        startTime = "N/A"
        stopTime = "N/A"
        tfmt = "%A, %B %d, %Y %I:%M:%S %p"
        key = "startedAt"
        if key in list(theJob.keys()):
            tTime = theJob[key]
            startTime = datetime.fromtimestamp((tTime/1000)).strftime(tfmt)
        key = "stoppedAt"
        if key in list(theJob.keys()):
            tTime = theJob[key]
            stopTime = datetime.fromtimestamp((tTime/1000)).strftime(tfmt)
        jobinfo["a. jobName"] = theJob["jobName"]
        jobinfo["j. jobQueue"] = theJob["jobQueue"]
        jobinfo["b. status"] = theJob["status"]
        statusinfo = "N/A"
        key = "reason"
        if key in list(theJob["container"].keys()):
            statusinfo = theJob["container"]["reason"]
        else:
            key = "statusReason"
            if key in list(theJob.keys()):
                statusinfo = theJob[key]
        jobinfo["c. status info"] = statusinfo
        jobinfo["d. jobId"] = theJob["jobId"]
        jobinfo["e. startedAt"] = startTime
        jobinfo["f. stoppedAt"] = stopTime
        jobinfo["g. memory"] = str(theJob["container"]["memory"])
        jobinfo["h. vcpus"] = str(theJob["container"]["vcpus"])
        jobinfo["i. image"] = theJob["container"]["image"]
        # check if array
        key = "arrayProperties"
        ikey = "k. arrayjob"
        if key in list(theJob.keys()):
            jobinfo[ikey] = "yes"
        else:
            jobinfo[ikey] = "no"
        if arrayProperties and jobinfo[ikey] == "yes":
            jid = theJob["jobId"]
            noTasks = theJob[key]["size"]
            arrayinfo = taskstat(batchC, jid, noTasks, verbose)

    results = [jobinfo, arrayinfo]

    return results

def jobdel(batchC, jobid, printout=False, verbose=False):
    # describe the job
    try:
        results = batchC.describe_jobs(jobs = [ jobid ])
    except Exception as e:
        print('describe_jobs exception ' + str(e))
        sys.exit(2)
    jobs = results['jobs']
    if len(jobs) == 0:
        print('jobid does not exist: '  + jobid)
        return
    job = jobs[0]
    if verbose:
        print('Debug jobdel - job describe: ' + str(job))
    # see if job is FAILED or SUCCEEDED
    if job["status"] == "FAILED":
        print('Job ' + jobid + " has FAILED and already terminated")
        return
    if job["status"] == "SUCCEEDED":
        print('Job ' + jobid + " has SUCCEEDED and already terminated")
        return
    # terminate
    if verbose:
        print('Debug jobdel - Terminating job id: ' + jobid)
    try:
        batchC.terminate_job( jobId = jobid, reason = "Request to terminate")
    except Exception as e:
        print('terminate_job exception ' + str(e))
        sys.exit(2)
    print("Requested job to terminate: " + jobid)

# parse input
parser = ArgumentParser( description = "Get the statuses of jobs or terminate jobs from the job info file" )
parser.add_argument( "jobinfo", nargs = 1, help = "jobinfo file or job id" )
parser.add_argument( "-p", "--profile", default = "nhlbi_compute", help = "aws profile")
parser.add_argument( "-a", "--arraydetails", action="store_true", default = False,
                     help = "describe array details (if applicable) for specified job id [default: False]" )
parser.add_argument( "-t", "--terminate", action="store_true", default = False,
                     help = "terminate either all the jobs in the job info file or the specified job id [default: False]" )
parser.add_argument( "-D", "--Debug", action="store_true", default = False,
                     help = "Turn on verbose output [default: False]" )
args = parser.parse_args()
jobinfo = args.jobinfo
jobinfo = jobinfo[0]
profile = args.profile
arraydetails = args.arraydetails
terminate = args.terminate
debug = args.Debug
# see if argument is a file; if not assume it's a job id
if os.path.isfile(jobinfo):
    idflag = False;
else:
    idflag = True;

if not idflag:
    # read the job info file and create a list of dicts
    print("Reading jobinfo file " + jobinfo)
    jobslist = []
    with open(jobinfo, "r") as jfile:
        for line in jfile:
            ll = line.split()
            # get the keys (field with ':')
            kp = [s for s in ll if any(':' in i for i in s)]
            keys = [s.strip(':') for s in kp]
            # get the vals
            vals = [s for s in ll if not any(':' in i for i in s)]
            # create a dict and append to the jobslist
            jdict = dict(list(zip(keys, vals)))
            if len(jdict) == 0:
                continue
            jobslist.append(jdict)
    if len(jobslist) == 0:
        print('Error: jobinfo file format is not valid')
        sys.exit(2)
else:
    jobid = jobinfo

try:
    session = boto3.Session(profile_name = profile)
    batchC = session.client('batch')

except Exception as e:
    print('boto3 session or client exception ' + str(e))
    sys.exit(2)
# get the list of job ids
if debug:
    if not idflag:
        print('Debug - no of jobs in jobslist: ' + str(len(jobslist)))
    else:
        print('Debug - job id: ' + jobid)

if not idflag:
    # process jobinfo file
    jids = [jd['jobId'] for jd in jobslist]

    # process the job ids
    jstats = proc_jobids(batchC, jids, terminate, debug)

    if not terminate:
        # print out stats
        if len(jstats) == 0:
            print("No jobs found  in : " + jobinfo)
            print("\tJob IDs: " + str(jids))
            sys.exit(0)
        print('Jobs status:')
        jstats.sort()
        for jd in jstats:
            print(jd)
else:
    # process the jobid
    if not terminate:
        # describe the job
        results = jobstat(batchC, jobid, arraydetails, verbose = debug)
        jobinfo = results[0]
        if len(jobinfo) == 0:
            print("job not found : " + jobid)
            sys.exit(2)
        print("jobinfo: ")
        for key in sorted(jobinfo.keys()):
            print("\t" + key + ": " + jobinfo[key])
        arrayinfo = results[1]
        if len(arrayinfo) > 0:
            print("arrayinfo:")
            for task in arrayinfo:
                for key in sorted(task.keys()):
                    print("\t" + key + ": " + task[key])
    else:
        jobdel(batchC, jobid, printout = True, verbose = debug)
