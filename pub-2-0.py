import time
import subprocess
import os

PUBLISH = ["bash", "workflow.sh"]


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


def main():
    run = True
    count = 0
    print("USER WARNING: This job will continue to run until stopped. Use Ctrl-C to quit job.")
    while run:
        try:
            count = len(os.listdir("/p/user_pub/publish-queue/CMIP6-maps-todo"))
        except:
            print("Filesystem error likely. Will attempt to resume in 5 minutes.")
            time.sleep(300)
            continue
        if count == 0:
            print("No maps left to do. Going to sleep.")
            time.sleep(1000)
            continue
        p = subprocess.Popen(PUBLISH)
        ec = None
        while ec is None:
            ec = p.poll()

        if ec == 0:
            print("Publisher moved new files. Resuming.")
            count = 0
        elif ec == 255:
            print("Stale file handle error. Will attempt to resume in 5 minutes.")
            time.sleep(300)
            count = 0
        else:
            print("Some other error: " + str(ec))
            count += 1
            if count > 3:
                print("Exit with error status: " + str(ec))
                send_msg("Publisher stopped with error status: " + str(ec), "e.witham@columbia.edu")
                exit(ec)
            else:
                print("Attempting to resume...")


if __name__ == '__main__':
    main()
