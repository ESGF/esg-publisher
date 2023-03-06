import time
from datetime import datetime
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
import sys
import tarfile
import argparse

import traceback

def get_args():
    parser = argparse.ArgumentParser(description="CMIP6 production replica publishing to ESGF database.")

    parser.add_argument("--debug", dest="debug", action="store_true", default=False,
                        help="Enable debug mode, print debug statements.")
    parser.add_argument("--cmor-tables", dest="cmor_tables", required=True,
                        help="Full path to CMOR tables directory.")
    parser.add_argument("--enable-errata", dest="errata", default=False, action="store_true",
                        help="Enable checking of the Errata database for failed mapfiles.")
    parser.add_argument("--check-latest", dest="check_latest", default=False, action="store_true",
                        help="Enable querying of ESGF database to ensure map is latest version upon failure.")
    parser.add_argument("--flag-file", dest="flag_file", required=True,
                        help="Path to (empty) flag file which will stop publisher if it contains 'stop'.")
    parser.add_argument("--success-directory", dest="success_dir", default="/p/user_pub/publish-queue/CMIP6-maps-done/",
                        help="Override directory to which successfully published mapfiles are moved.")
    parser.add_argument("--fail-directory", dest="fail_dir", default="/p/user_pub/publish-queue/CMIP6-maps-err/",
                        help="Override directory to which mapfiles which failed to publish are moved.")
    parser.add_argument("--tmp-dir", dest="tmp_dir", default="/p/user_pub/publish-queue/CMIP6-tmplogs/",
                        help="Override temporary directory for logs.")
    parser.add_argument("--fail-logs", dest="fail_logs", default="/esg/log/publisher/",
                        help="Override directory to which logs for failed mapfiles are moved.")
    parser.add_argument("--mapfile-path", dest="map_path", default="/p/user_pub/publish-queue/CMIP6-maps-todo/",
                        help="Override directory where mapfiles are pulled from.")
    parser.add_argument("--tarball-directory", dest="tar_dir", default="/p/user_pub/publish-queue/CMIP6-map-tarballs/",
                        help="Override directory where tarballs of published mapfiles are stored.")
    parser.add_argument("--incomplete-directory", dest="inc_dir", default="/p/user_pub/publish-queue/CMIP6-maps-inc/",
                        help="Override directory where incomplete mapfiles are moved to.")
    parser.add_argument("--email", dest="email", default="ames4@llnl.gov",
                        help="Primary email to send failure alerts, errors, and warnings to.")
    parser.add_argument("--llnl-email", dest="llnl_email", default="ames4@llnl.gov",
                        help="LLNL email address for SMTP to send alerts from.")
    parser.add_argument("-i", "--ini", dest="ini_file", required=True,
                        help="Override config file for publication. Please use complete file path.")

    args = parser.parse_args()
    return args


args = get_args()
FLAG_FILE = args.flag_file
SUCCESS_DIR = args.success_dir
FAIL_DIR = args.fail_dir
TMP_DIR = args.tmp_dir
ERROR_LOGS = args.fail_logs
MAP_PREFIX = args.map_path
ERR_PREFIX = args.fail_dir
TAR_DIR = args.tar_dir
ERRATA = args.errata
CHECK_LATEST = args.check_latest
CMOR_PATH = args.cmor_tables[:-1]
DEBUG = args.debug
LLNL_EMAIL = args.llnl_email
EMAIL = args.email
INI_FILE = args.ini_file
INC_DIR = args.inc_dir
print(INI_FILE)

def check_errata(pid):
    get_error = "http://errata.es-doc.org/1/resolve/simple-pid?datasets={}".format(pid)
    try:
        resp = json.loads(requests.get(get_error, timeout=120, verify=False).text)
    except:
        print("Could not reach errata site.")
        return False
    try:
        errata = resp[next(iter(resp))]["hasErrata"]
    except:
        print("Errata site threw error.")
        return False
    if errata:
        uid = str(resp[next(iter(resp))]["errataIds"][0])
        get_desc = "http://errata.es-doc.org/1/issue/retrieve?uid={}".format(uid)
        try:
            resp2 = json.loads(requests.get(get_desc, timeout=120, verify=False).text)
            desc = resp2["issue"]["description"]
            print("Errata found: " + desc)
            return True
        except:
            print("Could not get description from Errata site.")
            return True
    else:
        print("No existing errata for this dataset.")
        return False


def check_latest(pid):
    get_meta = "https://esgf-node.llnl.gov/esg-search/search?format=application%2fsolr%2bjson&instance_id={}&fields=retracted,latest".format(pid)
    try:
        resp = json.loads(requests.get(get_meta, timeout=120).text)
        if resp["response"]["numFound"] == 0:
            print(pid)
            print("No original record found.")
            return "missing"
        latest = resp["response"]["docs"][0]["latest"]
        retracted = resp["response"]["docs"][0]["retracted"]
        if not latest or retracted:
            print("Superseded by later version.")
            return "superseded"
        else:
            print("Dataset is current version.")
            return "current"
    except Exception as ex:
        print("Error fetching from esg-search api.")
        return "error"


def send_msg(message, to_email):
    print("Sending email...")
    msg = MIMEMultipart()
    from_email = LLNL_EMAIL
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


def archive_maps(files):
    print("Archiving maps...", file=sys.stderr, flush=True)
    thedate = datetime.now()
    fn = "mapfiles-" + str(thedate.strftime("%Y%m%d"))
    # tar command
    tar_job = subprocess.Popen(["tar", "-czf", TAR_DIR + fn, SUCCESS_DIR])
    try:
        tar_job.wait(timeout=600)
    except Exception as ex:
        print("ERROR: could not archive mapfiles: " + str(ex), file=sys.stderr, flush=True)
        return
    # remove maps
    os.TAR_DIR + fn
    for mf in files:
        os.remove(SUCCESS_DIR + mf)


def main():
    run = True
    count = 0
    last_err_count = -1
    redo_errs = False
    errs_done = False
    print("USER WARNING: This job will continue to run until stopped. Use text file flag to quit job.", file=sys.stderr, flush=True)
    while run:
        if DEBUG:
            print("outside loop", file=sys.stderr, flush=True)
        check_flag()
        try:
            files = os.listdir(MAP_PREFIX)
            count = len(files)
            done_files = os.listdir(SUCCESS_DIR)
            done_count = len(done_files)
        except:
            print("Filesystem error likely. Will attempt to resume in 5 minutes.", file=sys.stderr, flush=True)
            time.sleep(300)
            continue
        if done_count >= 100000:
            archive_maps(done_files)
        if count == 0 and not redo_errs:
            print("No maps left to do.", file=sys.stderr, flush=True)
            if not errs_done:
                print("Re checking errors...", file=sys.stderr, flush=True)
                redo_errs = True
                continue
            print("Going to sleep.", file=sys.stderr, flush=True)
            time.sleep(1000)
            continue
        check_flag()
        if redo_errs:
            try:
                files = os.listdir(ERR_PREFIX)
                count = len(files)
                print(f"redo_errs: {count} files found") 
                if count == 7 or count == last_err_count:
                    print("No unsorted errors left to retry.", file=sys.stderr, flush=True)
                    errs_done = True
                    redo_errs = False
                    continue
                else:
                    count -= 7
                last_err_count = count
            except:
                print("Filesystem error likely. Will attempt to resume in 5 minutes.", file=sys.stderr, flush=True)
                time.sleep(300)
                continue
        jobs = []
        logs = []
        p_list = []
        maps = []
        timeout = []
        for f in files:
            check_flag()
            if redo_errs:
                fullmap = ERR_PREFIX + f
            else:
                fullmap = MAP_PREFIX + f
            if DEBUG:
                print(f"file loop {fullmap}", file=sys.stderr, flush=True)
            if fullmap[-4:] != ".map":
                if ".part" in fullmap:
                    try:
                        shutil.move(fullmap, INC_DIR)
                    except Exception as ex:
                        if 'already exists' in str(ex):
                            os.remove(fullmap)
                    continue
                elif "greyworm" in f:
                    os.remove(fullmap)
                    continue
                elif f == files[-1]:
                    send_msg("Infinite loop detected, filename: " + f, EMAIL)
                    exit(1)
                else:
                    continue
            elif DEBUG:
                print(f"Mapfile found {fullmap}")

            maps.append(fullmap)
            log = TMP_DIR + f + ".log"
            logs.append(log)
            pub_cmd = ["esgpublish", "--ini", INI_FILE, "--map", fullmap]
            jobs.append(pub_cmd)
            gotosleep = False
            check_flag()
            if len(jobs) >= 8 or len(jobs) == count:
                i = 0
                for cmd in jobs:
                    p_list.append(subprocess.Popen(cmd, stdout=open(logs[i], "a+"), stderr=open(logs[i], "a+")))
                    i += 1
                for p in p_list:
                    if DEBUG:
                        print("job loop", file=sys.stderr, flush=True)
                    try:
                        p.wait(timeout=1800)
                        timeout.append(False)
                    except:
                        now = datetime.now()
                        date = now.strftime("%m/%d/%Y %H:%M:%S")
                        print(date + " job timeout: " + str(p.args), file=sys.stderr, flush=True)
                        timeout.append(True)
                n = 0
                for log in logs:
                    if DEBUG:
                        print("log loop", file=sys.stderr, flush=True)
                    now = datetime.now()
                    date = now.strftime("%m/%d/%Y %H:%M:%S")
                    success = 0
                    autoc = False
                    pid = False
                    server = False
                    ac = False
                    filesystem = False
                    fullmap = maps[n]
                    if timeout[n]:
                        n += 1
                        continue
                    n += 1
                    with open(log, "r+") as l:
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
                            if "activity check failed" in line:
                                print("WARNING: Failed activity check or experiment id check", file=sys.stderr, flush=True)
                                ac = True
                        l.write(date)
                    fn = log.split("/")[-1]
                    m = fn[:-4]
                    l = fn
                    if success < 2:
                        if ".part" in log:
                            continue
                        print(date + " error " + fullmap, file=sys.stderr, flush=True)
                        iid = fn[:-8]
                        errata = False
                        latest_rc = None
                        if ERRATA:
                            errata = check_errata(iid)
                        if CHECK_LATEST:
                            latest_rc = check_latest(iid)
                        if latest_rc == "error":
                            time.sleep(120)
                            latest_rc = check_latest(iid)
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
                            print("pid error", file=sys.stderr, flush=True)
                        elif filesystem:
                            print("filesystem error", file=sys.stderr, flush=True)
                            gotosleep = True
                        elif server:
                            print("server error", file=sys.stderr, flush=True)
                        elif ac:
                            shutil.move(fullmap, FAIL_DIR + "activity_check/" + m)
                            shutil.move(log, ERROR_LOGS + "activity_check/" + l)
                        elif autoc:
                            print("autocurator error", file=sys.stderr, flush=True)
                            try:
                                shutil.move(fullmap, FAIL_DIR + "autocurator/" + m)
                                shutil.move(log, ERROR_LOGS + "autocurator/" + l)
                            except Exception as ex:
                                print("shutil error", file=sys.stderr, flush=True)
                                if 'already exists' in str(ex) or 'Destination path' in str(ex):
                                    os.remove(fullmap)
                                    os.remove(log)
                                else:
                                    send_msg(str(ex), EMAIL)
                                    exit(1)
                        elif redo_errs:
                            shutil.move(fullmap, FAIL_DIR + "misc/" + m)
                            shutil.move(log, ERROR_LOGS + "misc/" + l)
                        else:
                            try:
                                shutil.move(fullmap, FAIL_DIR + m)
                                shutil.move(log, ERROR_LOGS + l)
                            except Exception as ex:
                                if 'already exists' in str(ex) or 'Destination path' in str(ex):
                                    os.remove(fullmap)
                                    os.remove(log)
                                else:
                                    send_msg(str(ex), EMAIL)
                                    exit(1)
                    else:
                        print(date + " success: " + m, file=sys.stderr, flush=True)
                        try:
                            shutil.move(fullmap, SUCCESS_DIR + m)
                            os.remove(log)
                        except Exception as ex:
                            if 'already exists' in str(ex) or 'Destination path' in str(ex):
                                os.remove(fullmap)
                            else:
                                send_msg(str(ex), EMAIL)
                                exit(1)
                jobs = []
                logs = []
                p_list = []
                maps = []
                check_flag()
                if redo_errs:
                    print("rechecking errors.", file=sys.stderr, flush=True)
                    #redo_errs = False
                    #errs_done = True
                    #                    files = []
                    break
                if gotosleep:
                    print("Going to sleep to resolve filesystem/server error. Will resume in 10 minutes.", file=sys.stderr, flush=True)
                    time.sleep(600)
        check_flag()


if __name__ == '__main__':
    go = True
    while go:
        if DEBUG:
            print("main loop", file=sys.stderr, flush=True)
        try:
            main()
            time.sleep(300)
        except Exception as ex:
            traceback.print_exc()
            
            if "stale file handle" in str(ex):
                print("Filesystem error likely. Going to sleep", file=sys.stderr, flush=True)
                check_flag()
                time.sleep(600)
                continue
            elif "No such file or directory" in str(ex):
                print("error, attempting to list directory...", file=sys.stderr, flush=True)
                check_flag()
            send_msg(str(ex), EMAIL)
            go = False
