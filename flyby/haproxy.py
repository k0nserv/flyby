import logging
import subprocess
from threading import Thread
import time
from jinja2 import Environment, PackageLoader


logger = logging.getLogger(__name__)
metrics = logging.getLogger("metrics")


class Haproxy:

    process = None

    def __init__(self, config_path="/etc/haproxy/haproxy.cfg"):
        self.config_path = config_path
        self.command = ['/usr/sbin/haproxy', '-f', config_path, '-db', '-q']
        logger.debug("Haproxy initialised: {}".format(str(self.command)))

    def _filter_services(self, services):
        """
        Filter services and target groups that have backends attached, and
        distribute target group weight between backends
        """
        filtered_services = []
        for service in services:
            filtered_target_groups = []
            min_multiplier = 0
            target_groups = service.get("target_groups", [])
            # Math here:
            # 1 - Find which target group's per-backend weight is the biggest
            # 2 - Get the value that when multiplied by this weight gives 256
            # 3 - Multiply the per-backend weight of each target by this value
            # Result: gives the most precision in allocating weights for a service's backends
            #   by assigning 256 to the highest per-backend weight and set the rest
            #   of the weights relative to that
            for target_group in target_groups:
                weight = target_group.get("weight")
                if weight:
                    # ignore draining/drained backends
                    target_group["backends"] = [
                        b for b in target_group.get("backends", [])
                        if b.get("status", "").upper() == "HEALTHY"
                        ]
                    if target_group["backends"]:
                        value = 256 / (weight / len(target_group["backends"]))
                        min_multiplier = min(
                            min_multiplier,
                            value
                        ) if min_multiplier else value
            for target_group in target_groups:
                weight = target_group.get("weight")
                if weight and target_group["backends"]:
                    target_group["weight"] = min(256, max(
                        1, round(
                            min_multiplier * weight / len(target_group["backends"])
                        )
                    ))
                    filtered_target_groups.append(target_group)
            if filtered_target_groups:
                service["target_groups"] = filtered_target_groups
                filtered_services.append(service)
        return filtered_services

    def update(self, services, fqdn="flyby.example.com", resolvers=None):
        logger.debug("Updating HAProxy configs...")
        resolvers = resolvers if resolvers else []
        env = Environment(loader=PackageLoader('flyby', 'config'))
        template = env.get_template('haproxy.cfg.j2')
        c = template.render(fqdn=fqdn, services=self._filter_services(services), resolvers=resolvers)
        if self.config != c:
            logger.debug("Changed configs identified.")
            self.config = c
            self._run()
            logger.debug("HAProxy configs successfully updated.")
        else:
            logger.debug("HAProxy configs up-to-date. Nothing to do.")

    @property
    def config(self):
        logger.debug("Opening config file for reading: {}".format(self.config_path))
        with open(self.config_path, 'r') as f:
            logger.debug("Reading config from: {}".format(self.config_path))
            config = f.read()
            logger.debug("Config successfully read from file.")
            return config

    @config.setter
    def config(self, value):
        logger.debug("Opening config file for writing: {}".format(self.config_path))
        with open(self.config_path, 'w') as f:
            logger.debug("Writing config to: {}".format(self.config_path))
            f.write(value)
            logger.debug("Config successfully written to file.")

    def _run(self):
        def _wait_pid(p):
            if p:
                logger.debug("Terminating old HAProxy process...")
                start_time = time.time()
                pid = p.pid
                logger.debug("Waiting for HAProxy(PID:{}) to shut down...".format(str(pid)))
                p.wait()
                metrics.info('haproxy-shutdown.duration {}'.format(time.time() - start_time))
                logger.info("HAProxy(PID:{}) has been terminated".format(str(pid)))
            else:
                logger.debug("Old HAProxy process not found.")

        if Haproxy.process:
            # Reload haproxy
            logger.info("Reloading HAProxy...")
            command = self.command + ["-sf", str(Haproxy.process.pid)]
            process = subprocess.Popen(command)
            old_process = Haproxy.process
            logger.debug("Starting shutdown thread...")
            shutdown_thread = Thread(target=_wait_pid, args=(old_process,))
            shutdown_thread.start()
            logger.debug("Shutdown thread started ({}).".format(shutdown_thread.name))
            Haproxy.process = process
            logger.info(
                "HAProxy has been reloaded (PID: {}): {}".format(
                    str(Haproxy.process.pid), " ".join(command)
                )
            )
        else:
            # Launch haproxy
            logger.info("Launching HAProxy...")
            Haproxy.process = subprocess.Popen(self.command)
            logger.info(
                "HAProxy has been launched (PID: {}): {}".format(
                    str(Haproxy.process.pid), " ".join(self.command)
                )
            )
