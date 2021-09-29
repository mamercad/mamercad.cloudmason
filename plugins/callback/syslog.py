# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.plugins.callback import CallbackBase
from pprint import pprint
import yaml
import socket
import syslog
import json
import os
import datetime

__metaclass__ = type

DOCUMENTATION = """
  author: Mark Mercado (@mamercad)
  name: syslog
  type: aggregate
  requirements:
    - Allow in configuration C(callbacks_enabled = syslog) in C([default]).
    - The C(requests) Python library.
  short_description: Sends a summary to Syslog.
  description:
    - This is an ansible callback plugin that sends a summary to Syslog.
  options:
    syslog_host:
      required: false
      description: Syslog host
      default: 127.0.0.1
      env:
        - name: SYSLOG_HOST
      ini:
        - section: callback_syslog
          key: syslog_host
    syslog_port:
      required: false
      description: Syslog port
      default: 514
      type: int
      env:
        - name: SYSLOG_PORT
      ini:
        - section: callback_syslog
          key: syslog_port
    syslog_facility:
      required: false
      description: Syslog facility
      default: LOG_LOCAL5
      env:
        - name: SYSLOG_FACILITY
      ini:
        - section: callback_syslog
          key: syslog_facility
    syslog_priority:
      required: false
      description: Syslog priority
      default: LOG_INFO
      env:
        - name: SYSLOG_PRIORITY
      ini:
        - section: callback_syslog
          key: syslog_priority
    ansible_events:
      required: false
      description: Ansible events for which to notify on.
      default: v2_playbook_on_start,v2_playbook_on_task_start,v2_runner_on_ok,v2_runner_on_skipped,v2_runner_on_unreachable,v2_runner_on_failed,v2_playbook_on_stats
      env:
        - name: ANSIBLE_EVENTS
      ini:
        - section: callback_summary
          key: ansible_events
"""

class SyslogClient(object):
    def __init__(
        self,
        host="127.0.0.1",
        proto="udp",
        port=514,
        facility=syslog.LOG_LOCAL5,
        priority=syslog.LOG_INFO,
    ):

        self.host = host
        self.proto = proto
        self.port = port
        self.facility = facility
        self.priority = priority

        if self.proto == "udp":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send(self, message="Hello, World"):
        # data = "<{0}>{1}".format(self.priority, self.facility*8, message)
        # <34>1 2003-10-11T22:14:15.003Z mymachine.example.com su - - - 'su root' failed for lonvick on /dev/pts/8
        # ts = datetime.datetime.now().isoformat()
        self.socket.sendto(message.encode("utf-8"), (self.host, self.port))


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "syslog"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.overall_summary = {}
        self.current_plays = None
        self.current_task = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

        self.syslog_host = self.get_option("syslog_host")
        self.syslog_port = self.get_option("syslog_port")
        self.syslog_facility = self.get_option("syslog_facility")
        self.syslog_priority = self.get_option("syslog_priority")

        self.syslog = SyslogClient(host=self.syslog_host, port=self.syslog_port, facility=self.syslog_facility, priority=self.syslog_priority)

        self.ansible_events = self.get_option("ansible_events").split(",")

    def post_message(self, text, data, **kwargs):
        self._display.display(str(pprint(data)))
        self.syslog.send()

    def v2_playbook_on_start(self, playbook, **kwargs):
        _plays = playbook.get_plays()
        _msg = f"PLAY {_plays}"
        _text = "{0} {1}".format(_msg, "*" * (79 - len(_msg)))
        if "v2_playbook_on_start" in self.ansible_events:
            pass
        self.current_plays = str(_plays)

    def v2_playbook_on_task_start(self, task, **kwargs):
        _task_name = task.name
        _role_name = task._role
        if "v2_playbook_on_task_start" in self.ansible_events:
            pass
        self.current_task = _task_name
        self.current_role = _role_name

    def _runner_on(self, result, status, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = str(result._host)
        if "v2_runner_on_ok" in self.ansible_events:
            pass

        if _host not in self.overall_summary:
            self.overall_summary[_host] = []
        self.overall_summary[_host].append(
            {
                "role": self.current_role,
                "task": self.current_task,
                "result": [status, _result],
            }
        )

    def v2_runner_on_ok(self, result, **kwargs):
        self._runner_on(result, "ok")

    def v2_runner_on_skipped(self, result, **kwargs):
        self._runner_on(result, "skipped")

    def v2_runner_on_unreachable(self, result, **kwargs):
        self._runner_on(result, "unreachable")

    def v2_runner_on_failed(self, result, **kwargs):
        self._runner_on(result, "failed")

    def v2_playbook_on_stats(self, stats):
        _hosts = sorted(stats.processed.keys())
        _stats = []
        for _host in _hosts:
            summary = stats.summarize(_host)
            _statsline = " ".join(
                "{!s}={!r}".format(key, val) for (key, val) in summary.items()
            )
            _stats.append(f"{_host} : {_statsline}")

        if "v2_playbook_on_stats" in self.ansible_events:
            pass

        self.display_overall_summary(stats)

    def display_overall_summary(self, stats):
        syslog = {}

        _play_name = self.current_plays[1:-1]
        _stats = dict(stats.__dict__)

        total_hosts, passing_hosts, failing_hosts = 0, 0, 0

        overall_results = {
            "processed": [],
            "failures": [],
            "ok": [],
            "dark": [],
            "changed": [],
            "skipped": [],
            "rescued": [],
            "ignored": [],
            "custom": [],
        }

        last_result = {}

        for status, result in _stats.items():
            for host, count in result.items():
                overall_results[status].append(host)

        for host in sorted(self.overall_summary.keys()):
            last_task = self.overall_summary[host][-1]
            for k, v in last_task.items():
                if host not in last_result:
                    last_result[host] = {}
                last_result[host][k] = v

        processed_hosts = set()
        failures_hosts = set()
        ok_hosts = set()
        dark_hosts = set()
        skipped_hosts = set()
        rescued_hosts = set()
        ignored_hosts = set()
        custom_hosts = set()

        for status, hosts in overall_results.items():
            for host in hosts:
                if status == "processed":
                    processed_hosts.add(host)
                elif status == "failures":
                    failures_hosts.add(host)
                elif status == "ok":
                    ok_hosts.add(host)
                elif status == "dark":
                    dark_hosts.add(host)
                elif status == "skipped":
                    skipped_hosts.add(host)
                elif status == "rescued":
                    rescued_hosts.add(host)
                elif status == "ignored":
                    ignored_hosts.add(host)
                elif status == "custom":
                    custom_hosts.add(host)
                else:
                    raise Exception(f"unhandled status {status}")

        total_hosts = processed_hosts
        passing_hosts = ok_hosts - failures_hosts - dark_hosts
        failing_hosts = failures_hosts | dark_hosts

        syslog["total_hosts"] = list(total_hosts)
        syslog["passing_hosts"] = list(passing_hosts)
        syslog["failing_hosts"] = list(failing_hosts)

        syslog["processed_hosts"] = list(processed_hosts)
        syslog["failures_hosts"] = list(failures_hosts)
        syslog["ok_hosts"] = list(ok_hosts)
        syslog["dark_hosts"] = list(dark_hosts)
        syslog["skipped_hosts"] = list(skipped_hosts)
        syslog["rescued_hosts"] = list(rescued_hosts)
        syslog["ignored_hosts"] = list(ignored_hosts)
        syslog["custom_hosts"] = list(custom_hosts)

        success_pct = 0
        if len(total_hosts) > 0:
            success_pct = 100.0 * len(passing_hosts) / len(total_hosts)

        syslog["success_pct"] = success_pct

        syslog["play_name"] = _play_name

        syslog["last_result"] = {}
        for host in failing_hosts:
            syslog["last_result"][host] = {
                "role": last_result[host]["role"],
                "task": last_result[host]["task"],
                "result": {
                    "status": last_result[host]["result"][0].strip(),
                    "result": last_result[host]["result"][1].strip(),
                },
            }

        tower_host = os.environ.get("TOWER_HOST", os.environ.get("AWX_URL", ""))
        job_id = os.environ.get("JOB_ID", -1)

        syslog["tower_host"] = tower_host
        syslog["job_id"] = job_id

        self.post_message(text="overall summary", data=syslog)
