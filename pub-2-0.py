import time
import subprocess
import os
from subprocess import PIPE
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import requests
import json


FLAG_FILE = "/export/witham3/pub-internal/flag.txt"
SUCCESS_DIR = "/p/user_pub/publish-queue/CMIP6-maps-done/"
FAIL_DIR = "/p/user_pub/publish-queue/CMIP6-maps-err/"
TMP_DIR = "/export/witham3/tmplogs/"
ERROR_LOGS = "/esg/log/publisher/"
MAP_PREFIX = "/p/user_pub/publish-queue/CMIP6-maps-todo/"

CMOR_PATH = "/export/witham3/cmor"


def run_ac(input_rec):

    cv_path = "{}/CMIP6_CV.json".format(CMOR_PATH)

    jobj = json.load(open(cv_path))["CV"]

    sid_dict = jobj["source_id"]

    src_id = input_rec['source_id']
    act_id = input_rec['activity_drs']

    if src_id not in sid_dict:
        return False

    rec = sid_dict[src_id]

    return act_id in rec["activity_participation"]


def run_ec(rec):

    cv_path = "{}/CMIP6_CV.json".format(CMOR_PATH)

    act_id = rec['activity_drs']
    exp_id = rec['experiment_id']

    cv_table = json.load(open(cv_path, 'r'))["CV"]

    if exp_id not in cv_table['experiment_id']:
        return False
    elif act_id not in cv_table['experiment_id'][exp_id]['activity_id']:
        return False
    else:
        return True


def check_errata(pid):
    get_error = "http://errata.es-doc.org/1/resolve/simple-pid?datasets={}".format(pid)
    try:
        resp = json.loads(requests.get(get_error, timeout=120, verify=False).text)
    except:
        print("Could not reach errata site.")
        return False
    errata = resp[next(iter(resp))]["hasErrata"]
    if errata:
        uid = str(resp[next(iter(resp))]["errataIds"][0])
        get_desc = "errata.es-doc.org/1/issue/retrieve?uid={}".format(uid)
        resp2 = json.loads(requests.get(get_desc, timeout=120, verify=False).text)
        desc = resp2["issue"]["description"]
        print("Errata found: " + desc)
        return True
    else:
        print("No existing errata for this dataset.")
        return False


def check_latest(pid):
    get_meta = "https://esgf-node.llnl.gov/esg-search/search?format=application%2fsolr%2bjson&instance_id={}&fields=retracted,latest".format(pid)
    resp = json.loads(requests.get(get_meta, timeout=120).text)
    try:
        latest = resp["response"]["docs"][0]["latest"]
        retracted = resp["response"]["docs"][0]["retracted"]
        if not latest or retracted:
            print("Superseded by later version.")
            return "superseded"
        else:
            print("Dataset is current version.")
            return "current"
    except Exception as ex:
        if resp["response"]["numFound"] == 0:
            print("No original record found.")
            return "missing"
        else:
            print("Error fetching from esg-search api.")
            return "error"


def send_msg(message, to_email):
    print("Sending email...")
    msg = MIMEMultipart()
    from_email = "witham3@llnl.gov" # can replace with ames4@llnl.gov
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Publisher Failure"
    body = message
    msg.attach(MIMEText(body, 'plain'))
    s = smtplib.SMTP('nospam.llnl.gov')  # llnl smtp: nospam.llnl.gov
    s.ehlo()
    s.starttls()
    text = msg.as_string()
    s.sendmail(from_email, to_email, text)
    s.quit()
    print("Done.")


def check_flag():
    with open(FLAG_FILE, "r+") as ff:
        flag = ff.readline().strip()
    if flag == "stop":
        print("Stopped by flag file. Terminating.")
        exit(0)


def main():
    run = True
    count = 0
    print("USER WARNING: This job will continue to run until stopped. Use text file flag to quit job.")
    while run:
        check_flag()
        try:
            files = os.listdir("/p/user_pub/publish-queue/CMIP6-maps-todo")
            count = len(files)
        except:
            print("Filesystem error likely. Will attempt to resume in 5 minutes.")
            time.sleep(300)
            continue
        if count == 0:
            print("No maps left to do. Going to sleep.")
            time.sleep(1000)
            continue
        check_flag()
        jobs = []
        logs = []
        p_list = []
        maps = []
        timeout = []
        for f in files:
            fullmap = MAP_PREFIX + f
            if fullmap[-4:] != ".map":
                if ".part" in fullmap:
                    try:
                        shutil.move(fullmap, "/export/witham3/CMIP6-maps-inc/")
                    except Exception as ex:
                        if 'already exists' in str(ex):
                            os.remove(fullmap)
                    continue
                if "greyworm" in f:
                    os.remove(fullmap)
                    check_flag()
                    continue
            maps.append(fullmap)
            log = TMP_DIR + f + ".log"
            logs.append(log)
            pub_cmd = ["python3", "gen-five/src/python/pub-internal.py", "--map", fullmap]
            jobs.append(pub_cmd)
            gotosleep = False
            check_flag()
            if len(jobs) >= 8:
                i = 0
                for cmd in jobs:
                    p_list.append(subprocess.Popen(cmd, stdout=open(logs[i], "w+"), stderr=open(logs[i], "w+")))
                    i += 1
                for p in p_list:
                    try:
                        p.wait(timeout=600)
                        timeout.append(False)
                    except:
                        print("job timeout" + str(p.args))
                        timeout.append(True)
                n = 0
                for log in logs:
                    success = 0
                    autoc = False
                    pid = False
                    server = False
                    filesystem = False
                    fullmap = maps[n]
                    if timeout[n]:
                        n += 1
                        continue
                    n += 1
                    with open(log, "r") as l:
                        l.seek(0,0)
                        for line in l.readlines():
                            if "success" in line:
                                success += 1
                            if "AMQPConnectionError" in line:
                                pid = True
                            if "server encountered an unexpected condition" in line:
                                server = True
                            if "Stale file handle" in line:
                                filesystem = True
                            if "ERROR: Variable" in line:
                                autoc = True
                            if "Unable to open data" in line:
                                autoc = True
                            if "Failed ac check" in line or "Failed ec check" in line:
                                print("WARNING: Failed activity check or experiment id check")
                    fn = log[24:-8]
                    m = fn + ".map"
                    l = fn + ".log"
                    if success < 2:
                        if ".part" in log:
                            continue
                        print("error " + fullmap)
                        errata = check_errata(fn)
                        latest_rc = check_latest(fn)
                        if errata:
                            shutil.move(fullmap, FAIL_DIR + "errata/" + m)
                            shutil.move(log, ERROR_LOGS + "errata/" + l)
                        elif latest_rc == "superseded":
                            shutil.move(fullmap, FAIL_DIR + "superseded/" + m)
                            shutil.move(log, ERROR_LOGS + "superseded/" + l)
                        elif latest_rc == "missing":
                            shutil.move(fullmap, FAIL_DIR + "missing/" + m)
                            shutil.move(log, ERROR_LOGS + "missing/" + l)
                        elif pid:
                            print("pid error")
                        elif filesystem:
                            print("filesystem error")
                            gotosleep = True
                        elif server:
                            print("server error")
                        elif autoc:
                            print("autocurator error")
                            try:
                                shutil.move(fullmap, FAIL_DIR + "autocurator/" + m)
                                shutil.move(log, ERROR_LOGS + "autocurator/" + l)
                            except Exception as ex:
                                print("shutil error")
                                if 'already exists' in str(ex) or 'Destination path' in str(ex):
                                    os.remove(fullmap)
                                    os.remove(log)
                                else:
                                    send_msg(str(ex), 'e.witham@columbia.edu')
                                    exit(1)
                        else:
                            try:
                                shutil.move(fullmap, FAIL_DIR + m)
                                shutil.move(log, ERROR_LOGS + l)
                            except Exception as ex:
                                if 'already exists' in str(ex) or 'Destination path' in str(ex):
                                    os.remove(fullmap)
                                    os.remove(log)
                                else:
                                    send_msg(str(ex), 'e.witham@columbia.edu')
                                    exit(1)
                    else:
                        try:
                            shutil.move(fullmap, SUCCESS_DIR + m)
                            os.remove(log)
                        except Exception as ex:
                            if 'already exists' in str(ex) or 'Destination path' in str(ex):
                                os.remove(fullmap)
                            else:
                                send_msg(str(ex), 'e.witham@columbia.edu')
                                exit(1)
                jobs = []
                logs = []
                p_list = []
                maps = []
                check_flag()
                if gotosleep:
                    print("Going to sleep to resolve filesystem/server error. Will resume in 10 minutes.")
                    time.sleep(600)
        check_flag()


if __name__ == '__main__':
    go = True
    while go:
        try:
            main()
        except Exception as ex:
            if "stale file handle" in str(ex):
                print("Filesystem error likely. Going to sleep")
                check_flag()
                time.sleep(600)
                continue
            elif "No such file or directory" in str(ex):
                print("error, attempting to list directory...")
                check_flag()
                continue
            send_msg(str(ex), "e.witham@columbia.edu")
            go = False
