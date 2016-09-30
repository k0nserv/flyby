from validator import Validator
import re
from datetime import datetime, timedelta
import ntplib
import logging


class ValidHost(Validator):

    def __init__(self):
        self.err_message = "Not a valid host"
        self.not_message = ""
        self.compiled_ip = re.compile('\d+.\d+.\d+.\d+')

    def __call__(self, value):
        return self.compiled_ip.match(value) or self.is_valid_dns(value)

    def is_valid_dns(self, value):

        if len(value) > 255:
            self.err_message = "Url is greater than the 255 byte limit"
            return False

        return self.segments_are_valid(value)

    def segments_are_valid(self, value):
        for s in value.split("."):
            if len(s) > 63:
                self.err_message = "URL segment too long: {0}".format(s)
                return False

        return True


class ValidHostWithPort(ValidHost):

    def __init__(self):
        super().__init__()
        self.compiled_ip = re.compile('\d+.\d+.\d+.\d+:\d+')

    def is_valid_dns(self, value):
        """Overrides base class definition"""
        host, port = value.split(":")[-2:]
        if not self.check_port(port):
            return False

        if len(host) > 255:
            self.err_message = "Url is greater than the 255 byte limit"
            return False

        return self.segments_are_valid(host)

    def check_port(self, port):
        p = -1
        if not port:
            self.err_message = "Host has no port associated"
            return False

        try:
            p = int(port)
        except ValueError:
            self.err_message = "Host has no port associated"
            return False

        if 0 < p <= 65535:
            return True

        self.err_message = "Host has invalid port number"
        return False

    def segments_are_valid(self, value):
        for s in value.split("."):
            if len(s) > 63:
                self.err_message = "URL segment too long: {0}".format(s)
                return False

        return True


class NTP(object):
    _ntp_client = ntplib.NTPClient()
    _last_updated = None
    _current_offset = 0

    @classmethod
    def get_server_time(cls):
        now = datetime.now()
        if not cls._last_updated or (now > (cls._last_updated + timedelta(seconds=300))):
            cls._last_updated = now
            try:
                cls._current_offset = cls._ntp_client.request('pool.ntp.org').offset
            except Exception as e:
                logging.exception(e)
        return datetime.now() - timedelta(milliseconds=cls._current_offset)
