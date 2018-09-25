#! /usr/bin/env python

from bottle import route, run, response
import paramiko
import subprocess
import configparser

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


def send_wol(ip, mac):
    p = subprocess.Popen("wakeonlan -i %s -p 22 %s" % (ip, mac), shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return p.stdout.readlines()


def send_shutdown(ip, user, pw):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=user, password=pw)
    except paramiko.ssh_exception.NoValidConnectionsError:
        return "already shutdown"

    ssh.exec_command("shutdown -p now")
    return "shutting down NAS"


@route('/')
def default_route():
    response.status = 403
    return 'Forbidden'


@route('/start-nas/<key>')
def start_nas(key):
    if key != API_KEY:
        response.status = 401
        return 'wrong API Key'
    else:
        response.status = 200
        return send_wol(ConfigSectionMap("NAS")["ip"], ConfigSectionMap("NAS")["mac"])


@route('/stop-nas/<key>')
def stop_nas(key):
    if key != API_KEY:
        response.status = 401
        return 'wrong API Key'
    else:
        response.status = 200
        return send_shutdown(ConfigSectionMap("NAS")["ip"], ConfigSectionMap("NAS")["ssh_user"],
                             ConfigSectionMap("NAS")["ssh_pass"])


run(host=ConfigSectionMap("MAIN")["host"], port=ConfigSectionMap("MAIN")["port"],
    debug=ConfigSectionMap("MAIN")["debug"])




