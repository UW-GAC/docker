#! /usr/bin/env python
import os
import sys
import time

from       argparse import ArgumentParser

try:
    import boto3
except ImportError:
    print ("AWS batch not supported.")

def jobstat(batchC, jobid, verbose):
    jobinfo = {}
    # get the job status
    try:
        jinfo = batchC.describe_jobs(jobs = [ jobid ])
    except Exception as e:
        print('describe_jobs exception ' + str(e))
        sys.exit(2)
    # if found, get info
    if len(jinfo["jobs"]) > 0 :
        theJob = jinfo["jobs"][0]
        jobinfo["jobName"] = theJob["jobName"]
        jobinfo["jobQueue"] = theJob["jobQueue"]
        jobinfo["status"] = theJob["status"]
        jobinfo["jobId"] = theJob["jobId"]

    return jobinfo

def jobdel(batchC, jobid, wait, verbose):
    # get the job stat
    jobinfo = jobstat(batchC, jobid, verbose)
    if len(jobinfo) == 0:
        print('jobid does not exist: '  + jobid)
        sys.exit(2)
    # terminate
    try:
        batchC.terminate_job( jobId = jobinfo["jobId"], reason = "Request to terminate")
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
            jobinfo = jobstat(batchC, jobid, verbose)
            if len(jobinfo) == 0:
                print("job no longer exists: " + jobid)
                break
            else:
                if jobinfo["status"] == "FAILED":
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

try:
    session = boto3.Session(profile_name = profile)
    batchC = session.client('batch')

except Exception as e:
    print('boto3 session or client exception ' + str(e))
    sys.exit(2)

if describe:
    jobinfo = jobstat(batchC, jobid, verbose = debug)
    if len(jobinfo) == 0:
        print("job not found : " + jobid)
        sys.exit(2)
    print("jobinfo: ")
    print("\tstatus: " + jobinfo["status"])
    print("\tjob name: " + jobinfo["jobName"])
    print("\tqueue: " + jobinfo["jobQueue"])
    print("\tjob id: " + jobinfo["jobId"])

if terminate:
    jobdel(batchC, jobid, wait, verbose = debug)
