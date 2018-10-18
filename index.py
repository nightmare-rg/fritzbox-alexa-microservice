#! /usr/bin/env python

from bottle import Bottle, run, response
import paramiko
import configparser
import fritzctl
from requestlogger import WSGILogger, ApacheFormatter
from logging.handlers import TimedRotatingFileHandler
import os

app = Bottle()

config = configparser.ConfigParser()
config.read('config.ini')


def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print("test")
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


API_KEY = ConfigSectionMap("MAIN")["api_key"]


def wakeup_device(mac):
    s = fritzctl.Session(ConfigSectionMap("FRITZBOX")["host"], ConfigSectionMap("FRITZBOX")["user"],
                         ConfigSectionMap("FRITZBOX")["pass"])
    api = s.getOOAPI("general_hosts")

    api.wakeUp(str(mac))


def send_shutdown(ip, user, pw):

    nas_up = True if os.system("ping -c 1 " + ip) is 0 else False

    if nas_up:

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(ip, username=user, password=pw)
        except paramiko.ssh_exception.NoValidConnectionsError:
            return "No SSH Connection"

        ssh.exec_command("shutdown -p now")

        return "shutting down NAS"
    else:
        return "already down"


@app.route('/')
def default_route():
    response.status = 403
    return 'Forbidden'


@app.route('/start-nas/<key>')
def start_nas(key):
    if key != API_KEY:
        response.status = 401
        return 'wrong API Key'
    else:
        response.status = 200
        return wakeup_device(ConfigSectionMap("NAS")["mac"])


@app.route('/stop-nas/<key>')
def stop_nas(key):
    if key != API_KEY:
        response.status = 401
        return 'wrong API Key'
    else:
        response.status = 200
        return send_shutdown(ConfigSectionMap("NAS")["ip"], ConfigSectionMap("NAS")["ssh_user"],
                             ConfigSectionMap("NAS")["ssh_pass"])

handlers = [TimedRotatingFileHandler('access.log', 'd', 7), ]
app = WSGILogger(app, handlers, ApacheFormatter(), ip_header='HTTP_X_FORWARDED_FOR')

run(app, host=ConfigSectionMap("MAIN")["host"], port=ConfigSectionMap("MAIN")["port"],
    debug=ConfigSectionMap("MAIN")["debug"])
