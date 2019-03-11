#! /usr/bin/env python
import os
import sys
import time
from   datetime import datetime

from       argparse import ArgumentParser

try:
    import boto3
except ImportError:
    print ("AWS boto3 not installed.")
    sys.exit(2)

def taskstat(batchC, jobid, noTasks, verbose):
    taskinfo = []
    # get info on all tasks (<jobid>:<index>)
    for task in range(noTasks):
        tinfo = {}
        tid = jobid + ":" + str(task)
        if verbose:
            print("array job id: " + tid)
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
            if key in theJob.keys():
                tTime = theJob[key]
                startTime = datetime.fromtimestamp(tTime/1000).strftime(tfmt)
            key = "stoppedAt"
            if key in theJob.keys():
                tTime = theJob[key]
                stopTime = datetime.fromtimestamp(tTime/1000).strftime(tfmt)
            tinfo["a. task_id"] = tid
            tinfo["b. \tstart time"] = startTime
            tinfo["c. \tend time"] = stopTime
            tinfo["d. \tindex"] = index
            statusreason = "N/A"
            key = "statusReason"
            if key in theJob["container"].keys():
                statusreason = theJob["container"][key]
            tinfo["e. \tstatus"] = statusreason
            statusinfo = "N/A"
            key = "reason"
            if key in theJob["container"].keys():
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
            print("job info: \n")
            print(str(theJob))
        startTime = "N/A"
        stopTime = "N/A"
        tfmt = "%A, %B %d, %Y %I:%M:%S %p"
        key = "startedAt"
        if key in theJob.keys():
            tTime = theJob[key]
            startTime = datetime.fromtimestamp(tTime/1000).strftime(tfmt)
        key = "stoppedAt"
        if key in theJob.keys():
            tTime = theJob[key]
            stopTime = datetime.fromtimestamp(tTime/1000).strftime(tfmt)
        jobinfo["a. jobName"] = theJob["jobName"]
        jobinfo["j. jobQueue"] = theJob["jobQueue"]
        jobinfo["b. status"] = theJob["status"]
        statusinfo = "N/A"
        key = "reason"
        if key in theJob["container"].keys():
            statusinfo = theJob["container"]["reason"]
        else:
            key = "statusReason"
            if key in theJob.keys():
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
        if key in theJob.keys():
            jobinfo[ikey] = "yes"
        else:
            jobinfo[ikey] = "no"
        if arrayProperties and jobinfo[ikey] == "yes":
            jid = theJob["jobId"]
            noTasks = theJob[key]["size"]
            arrayinfo = taskstat(batchC, jid, noTasks, verbose)

    results = [jobinfo, arrayinfo]

    return results

def jobdel(batchC, jobid, wait, printout, verbose):
    # get the job stat

    results = jobstat(batchC, jobid, False, verbose)
    if len(results) == 0:
        print('jobid does not exist: '  + jobid)
        sys.exit(2)
    # terminate
    if verbose:
        print('Terminated job id: ' + jobid)
    try:
        batchC.terminate_job( jobId = jobid, reason = "Request to terminate")
    except Exception as e:
        print('terminate_job exception ' + str(e))
        sys.exit(2)
    print("requested job to terminate: " + jobid)
    # wait if desired
    if wait:
        maxTime = 60
        timeW = 0
        sTime = 2
        while True:
            results = jobstat(batchC, jobid, verbose)
            if len(results) == 0:
                print("job no longer exists: " + jobid)
                break
            else:
                jobinfo = results[0]
                if jobinfo["c. status info"] == "FAILED":
                    print("job terminated and in FAILED state: " + jobid)
                    break
            time.sleep(sTime)
            timeW += sTime
            if timeW > maxTime:
                print("Error terminate_job: job did not terminate before " + str(maxTime) + " seconds")
                sys.exit(2)

# parse input
parser = ArgumentParser( description = "script to test batchinit" )
parser.add_argument( "-j", "--jobid",
                     help = "Job id [required]" )
parser.add_argument( "-p", "--profile", default = "uw",
                     help = "aws profile")
parser.add_argument( "-d", "--describe", action="store_false", default = True,
                     help = "describe job state [default: True]" )
parser.add_argument( "-a", "--arrayproperties", action="store_true", default = False,
                     help = "describe array properties [default: False]" )
parser.add_argument( "-t", "--terminate", action="store_true", default = False,
                     help = "describe job state [default: False]" )
parser.add_argument( "-w", "--wait", action="store_true", default = False,
                     help = "wait for job to terminate [default: False]" )
parser.add_argument( "-D", "--Debug", action="store_true", default = False,
                     help = "Turn on verbose output [default: False]" )
args = parser.parse_args()
jobid = args.jobid
profile = args.profile
describe = args.describe
terminate = args.terminate
wait = args.wait
debug = args.Debug
arrayproperties = args.arrayproperties

try:
    session = boto3.Session(profile_name = profile)
    batchC = session.client('batch')

except Exception as e:
    print('boto3 session or client exception ' + str(e))
    sys.exit(2)

if describe:
    results = jobstat(batchC, jobid, arrayproperties, verbose = debug)
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

if terminate:
    jobdel(batchC, jobid, wait, describe, verbose = debug)
