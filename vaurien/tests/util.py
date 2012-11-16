import subprocess
import sys


def start_web_server(port=8888):
    cmd = [sys.executable, '-m', 'SimpleHTTPServer', str(port)]
    server = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    return server
