# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
author: Mark Mercado (@mamercad)
name: mamercad.cloudmason.statsd
type: notification
requirements:
  - Python C(os), and C(socket) libraries.
short_description: Send Ansible playbook result metrics to a StatsD (or StatsD Prometheus Exporter) endpoint.
description:
  - Send Ansible playbook result metrics to a StatsD (or StatsD Prometheus Exporter) endpoint.
options:
  statsd_host:
    name: StatsD hostname or IP
    default: 127.0.0.1
    description: StatsD hostname or IP to send metrics to
    env:
      - name: STATSD_HOST
    ini:
      - section: callback_statsd
        key: statsd_host
  statsd_port:
    name: StatsD metric port
    default: 9125
    description: StatsD TCP metric ingestion port
    env:
      - name: STATSD_PORT
    ini:
      - section: callback_statsd
        key: statsd_port
"""

import socket
import base64

from ansible.plugins.callback import CallbackBase
from ansible import constants as C
from __main__ import cli


class StatsD:
    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host")
        self.port = kwargs.get("port")
        self.basedir = None
        self.playbook = None

    def ship_it(self, parent, metric):
        """ Sends the metric to StatsD """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, int(self.port)))
            sock.sendall(metric.encode())
            if parent._display.verbosity:
                parent._display.display(f"Sent metric {metric} to StatsD at {self.host}:{self.port}")
        except Exception as e:
            if parent._display.verbosity:
                parent._display.display(f"Failed to sent metric {metric} to StatsD at {self.host}:{self.port} ({e})")
        finally:
            sock.close()

    def v2_playbook_on_start(self, parent, playbook, plays):
        """ Constructs the StatsD metric for sending """
        self.playdir = base64.b64encode(playbook["_basedir"].encode("utf-8")).decode("utf-8")
        self.playbook = playbook["_file_name"].replace(".", "_") # e.g., replace ".yml" with "_yml"
        self.plays = base64.b64encode(str(plays).encode("utf-8")).decode("utf-8")
        metric = "ansible.v2_playbook_on_start.{0}.{1}.{2}:1|c".format(
            self.playdir,
            self.playbook,
            self.plays,
        )
        if parent._display.verbosity:
            parent._display.display(f"metric: {metric}")
        self.ship_it(parent, metric)

    def v2_runner_on_ok(self, parent, result):
        """ Constructs the StatsD metric for sending """
        metric = "ansible.v2_runner_on_ok.{0}.{1}.{2}.{3}.{4}:1|c".format(
            self.playdir,
            self.playbook,
            result["_host"],
            str(result["_task"]).replace("TASK: ", ""),
            result["_result"]["changed"],
        )
        if parent._display.verbosity:
            parent._display.display(f"metric: {metric}")
        self.ship_it(parent, metric)

    def v2_runner_on_failed(self, parent, result):
        """ Constructs the StatsD metric for sending """
        metric = "ansible.v2_runner_on_failed.{0}.{1}.{2}.{3}.{4}:1|c".format(
            self.playdir,
            self.playbook,
            result["_host"],
            str(result["_task"]).replace("TASK: ", ""),
            result["_result"]["changed"],
        )
        if parent._display.verbosity:
            parent._display.display(f"metric: {metric}")
        self.ship_it(parent, metric)

    def v2_runner_on_skipped(self, parent, result):
        """ Constructs the StatsD metric for sending """
        metric = "ansible.v2_runner_on_skipped.{0}.{1}.{2}.{3}.{4}:1|c".format(
            self.playdir,
            self.playbook,
            result["_host"],
            str(result["_task"]).replace("TASK: ", ""),
            result["_result"]["changed"],
        )
        if parent._display.verbosity:
            parent._display.display(f"metric: {metric}")
        self.ship_it(parent, metric)

    def v2_runner_on_unreachable(self, parent, result):
        """ Constructs the StatsD metric for sending """
        metric = "ansible.v2_runner_on_unreachable.{0}.{1}.{2}.{3}.{4}:1|c".format(
            self.playdir,
            self.playbook,
            result["_host"],
            str(result["_task"]).replace("TASK: ", ""),
            result["_result"]["changed"],
        )
        if parent._display.verbosity:
            parent._display.display(f"metric: {metric}")
        self.ship_it(parent, metric)

    def v2_playbook_on_stats(self, parent, stats):
        """ Constructs the StatsD metric for sending """
        for k1 in stats.keys():
            if len(stats[k1]):
                for k2 in stats[k1].keys():
                    metric = "ansible.v2_playbook_on_stats.{0}.{1}.{2}.{3}:1|c".format(
                        self.playdir,
                        self.playbook,
                        k1,
                        k2,
                    )
                    if parent._display.verbosity:
                        parent._display.display(f"metric: {metric}")
                    self.ship_it(parent, metric)


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "mamercad.cloudmason.statsd"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

        self.statsd_host = self.get_option("statsd_host")
        self.statsd_port = self.get_option("statsd_port")

        if self._display.verbosity:
            self._display.display(
                f"*** statsd callback plugin settings ***", color=C.COLOR_DEBUG
            )
            self._display.display(f"statsd_host: {self.statsd_host}", color=C.COLOR_DEBUG)
            self._display.display(f"statsd_port: {self.statsd_port}", color=C.COLOR_DEBUG)

        self.statsd = StatsD(host=self.statsd_host, port=self.statsd_port)

    def v2_playbook_on_start(self, playbook, **kwargs):
        if self._display.verbosity:
            self._display.display("*** v2_playbook_on_start ***", color=C.COLOR_DEBUG)
            self._display.display(str(playbook.__dict__), color=C.COLOR_DEBUG)
        self.statsd.v2_playbook_on_start(self, playbook.__dict__, playbook.get_plays())

    def v2_playbook_on_play_start(self, play, **kwargs):
        self.play = play
        self.extra_vars = self.play.get_variable_manager().extra_vars
        if self._display.verbosity:
            self._display.display(
                "*** v2_playbook_on_play_start ***", color=C.COLOR_DEBUG
            )
            self._display.display(str(play.__dict__), color=C.COLOR_DEBUG)
            self._display.display(str(self.extra_vars), color=C.COLOR_DEBUG)
        # Not emitting any metrics for this yet

    def v2_runner_on_ok(self, result, **kwargs):
        if self._display.verbosity:
            self._display.display("*** v2_runner_on_ok ***", color=C.COLOR_DEBUG)
            self._display.display(str(result.__dict__), color=C.COLOR_DEBUG)
        self.statsd.v2_runner_on_ok(self, result.__dict__)

    def v2_runner_on_failed(self, result, **kwargs):
        if self._display.verbosity:
            self._display.display("*** v2_runner_on_failed ***", color=C.COLOR_DEBUG)
            self._display.display(str(result.__dict__), color=C.COLOR_DEBUG)
        self.statsd.v2_runner_on_failed(self, result.__dict__)

    def v2_runner_on_skipped(self, result, **kwargs):
        if self._display.verbosity:
            self._display.display("*** v2_runner_on_skipped ***", color=C.COLOR_DEBUG)
            self._display.display(str(result.__dict__), color=C.COLOR_DEBUG)
        self.statsd.v2_runner_on_skipped(self, result.__dict__)

    def v2_runner_on_unreachable(self, result, **kwargs):
        if self._display.verbosity:
            self._display.display("*** v2_runner_on_unreachable ***", color=C.COLOR_DEBUG)
            self._display.display(str(result.__dict__), color=C.COLOR_DEBUG)
        self.statsd.v2_runner_on_unreachable(self, result.__dict__)

    def v2_playbook_on_stats(self, stats, **kwargs):
        if self._display.verbosity:
            self._display.display("*** v2_playbook_on_stats ***", color=C.COLOR_DEBUG)
            self._display.display(str(stats.__dict__), color=C.COLOR_DEBUG)
        self.statsd.v2_playbook_on_stats(self, stats.__dict__)
