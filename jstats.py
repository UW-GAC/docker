#! /usr/bin/env python
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
        print('jid: ' + jid)
        print('no. tasks: ' + str(noTasks))
    # build a list of task ids
    tids = createtaskids(jid, noTasks)
    if verbose:
        print("task ids: " + str(tids))
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

def jobstat(batchC, jobids, verbose):
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
    if noJobs > 0:
        jobs = jinfo["jobs"]
        for job in jobs:
            jd = {}
            if verbose:
                print("job info: \n")
                print(str(job))
            jobtype = "single"
            jobstatus = job['status']
            if "arrayProperties" in job.keys():
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

# parse input
parser = ArgumentParser( description = "script to test batchinit" )
parser.add_argument( "-j", "--jobinfo",
                     help = "jobinfo file [required]" )
parser.add_argument( "-p", "--profile", default = "uw",
                     help = "aws profile")
parser.add_argument( "-a", "--arraystatus", action="store_true", default = False,
                     help = "describe array status [default: False]" )
parser.add_argument( "-D", "--Debug", action="store_true", default = False,
                     help = "Turn on verbose output [default: False]" )
args = parser.parse_args()
jobinfo = args.jobinfo
profile = args.profile
arraystatus = args.arraystatus
debug = args.Debug

# check if ji file exists
if not os.path.isfile(jobinfo):
    print('Error: jobinfo file ' + jobinfo + ' does not exist.')
    sys.exit(2)

# read the job info file and create a list of dicts
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
        jdict = dict(zip(keys, vals))
        if len(jdict) == 0:
            continue
        if debug:
            print('Debug: job ' + str(jdict) )
        jobslist.append(jdict)
if len(jobslist) == 0:
    print('Error: jobinfo file format is not valid')
    sys.exit(2)

try:
    session = boto3.Session(profile_name = profile)
    batchC = session.client('batch')

except Exception as e:
    print('boto3 session or client exception ' + str(e))
    sys.exit(2)
# get the list of job ids
if debug:
    print('jobslist: ' + str(jobslist))
jids = [jd['jobId'] for jd in jobslist]

# get status
jstats = jobstat(batchC, jobids = jids, verbose = debug)

# print out stats
if len(jstats) == 0:
    print("No jobs found  : " + str(jids))
    sys.exit(0)
print('Jobs status:')
jstats.sort()
for jd in jstats:
    print(jd)
