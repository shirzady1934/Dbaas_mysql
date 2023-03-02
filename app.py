import sys
import time
import json
import flask
import string
import socket
import random
import pickle
import hashlib
import subprocess

app = flask.Flask('__init__')

pbase = 8000
cntr = 0

def load_data():
    global cntr
    global pbase
    try:
        with open('saved.pk', 'rb') as f:
            cntr = pickle.load(f)
            pbase = 8000 + cntr
        if cntr > 0:
            for i in range(cntr):
                subprocess.Popen("docker restart db%d" % i)
    except:
        pass

load_data()

@app.route('/getdb', methods=['POST'])
def getdb():
    global pbase
    global cntr
    token = flask.request.form.get('token')
    if token == None:
        return flask.Response('no token!')

    sha = hashlib.sha256(token.strip().encode()).hexdigest()
    if sha != '936a185caaa266bb9cbe981e9e05cb78cd732b0b3280eb944412bb6f8f8f07af':
        return flask.Response('Wrong token')
    try:
        os.mkdir("/tmp/db%d" % cntr);
    except:
        pass
    generatedpass = ''.join(random.choices((string.ascii_letters + string.digits), k=15))
    cmd = "docker run -d -e MYSQL_ROOT_PASSWORD=%s --name=db%d -p %d:3306 -v /tmp/db%d:/var/lib/mysql --rm mysql/mysql-server" % (generatedpass, cntr, pbase, cntr)
    rt = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rtc = rt.wait()
    if rtc != 0:
        return flask.Response("503")
    rs = False
    while not rs:
        rs = subprocess.Popen('docker logs db%d &> >(grep "Plugin ready for connections. Bind-address: \'::\' port: 33060")' % cntr, shell=True, stdout=subprocess.PIPE)
        rs = rs.stdout.read()
        time.sleep(1)
    #rqip = flask.request.remote_addr
    #subprocess.Popen('docker exec -it db%d mysql  -uroot -p"%s" -Bse "CREATE USER \'user%d\'@\'%s\' identified by \'%s\'; CREATE DATABASE db%d; GRANT ALL PRIVILEGES ON *.* TO \'user%d\'@\'%s\'; FLUSH PRIVILEGES;"' % (cntr, generatedpass, cntr, rqip, generatedpass, cntr, cntr, rqip), shell=True)
    subprocess.Popen('docker exec -it db%d mysql -uroot -p"%s" -Bse "CREATE USER user%d identified by \'%s\'; CREATE DATABASE db%d; GRANT ALL PRIVILEGES ON *.* TO user%d; FLUSH PRIVILEGES;"' % (cntr, generatedpass, cntr, generatedpass, cntr, cntr), shell=True)
    subprocess.Popen("firewall-cmd --add-port=%d/tcp --permanent; firewall-cmd --reload;" % pbase, shell=True);

    ip = socket.gethostbyname(socket.gethostname())
    rss = dict()
    rss['ip'] = ip
    rss['port'] = pbase
    rss['user'] = 'user%d' % cntr
    rss['password'] = generatedpass
    rss['database'] = 'db%d' % cntr
    pbase += 1
    cntr += 1
    with open('saved.pk', 'wb') as f:
        pickle.dump(cntr, f)
    return flask.Response(json.dumps(rss))

if __name__ == '__main__':
    app.run("0.0.0.0")
