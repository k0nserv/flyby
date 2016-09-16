import logging
import subprocess
import _thread
import time
from jinja2 import Environment, PackageLoader


logger = logging.getLogger("haproxy")
metrics = logging.getLogger("metrics")


class Haproxy:

    process = None

    def __init__(self, config_path="/etc/haproxy/haproxy.cfg"):
        self.config_path = config_path
        self.command = ['/usr/sbin/haproxy', '-f', config_path, '-db', '-q']

    def update(self, services, fqdn="flyby.example.com"):
        env = Environment(loader=PackageLoader('flyby', 'config'))
        template = env.get_template('haproxy.cfg.j2')
        c = template.render(fqdn=fqdn, services=services)
        if self.config != c:
            self.config = c
            self._run()

    @property
    def config(self):
        with open(self.config_path, 'r') as f:
            return f.read()

    @config.setter
    def config(self, value):
        with open(self.config_path, 'w') as f:
            return f.write(value)

    def _run(self):
        def _wait_pid(p):
            if p:
                start_time = time.time()
                pid = p.pid
                p.wait()
                metrics.info('haproxy-shutdown.duration {}'.format(time.time() - start_time))
                logger.info("HAProxy(PID:{}) has been terminated".format(str(pid)))

        if Haproxy.process:
            # Reload haproxy
            logger.info("Reloading HAProxy")
            process = subprocess.Popen(
                self.command + ["-sf", str(Haproxy.process.pid)]
            )
            old_process = Haproxy.process
            _thread.start_new_thread(_wait_pid, (old_process,))
            Haproxy.process = process
            logger.info(
                "HAProxy has been reloaded(PID: {})".format(str(Haproxy.process.pid)))
        else:
            # Launch haproxy
            logger.info("Launching HAProxy")
            Haproxy.process = subprocess.Popen(self.command)
            logger.info(
                "HAProxy has been launched(PID: {})".format(str(Haproxy.process.pid)))
