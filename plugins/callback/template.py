# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
  author: Mark Mercado (@mamercad)
  name: mamercad.cloudmason.template
  type: notification
  requirements:
    - Allow in configuration C(callbacks_enabled = mamercad.cloudmason.template) in C([default]).
  short_description: This is an Ansible template callback plugin.
  description:
    - This is an Ansible template callback plugin.
  options:
    ansible_events:
      required: false
      description: Ansible events for which to notify on.
      default: v2_playbook_on_start,v2_playbook_on_task_start,v2_runner_on_ok,v2_runner_on_skipped,v2_runner_on_unreachable,v2_runner_on_failed,v2_playbook_on_stats
      env:
        - name: ANSIBLE_EVENTS
      ini:
        - section: callback_slack
          key: ansible_events
"""

import json
from pprint import pprint

from ansible.plugins.callback import CallbackBase


class Porcelain(object):

    def __init__(self):
        pass

    def dump(self, parent):
        print = parent._display.display
        print("#"*80)
        playbook = parent.ansible["playbook"]
        for k in playbook:
            print(f"{k} ({str(type(playbook[k]))}) {str(playbook[k])}")
        print("#"*80)


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "mamercad.cloudmason.template"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.ansible = {}
        self.ansible["playbook"] = {}
        self.ansible["tasks"] = []
        self.ansible["results"] = {}  # keyed by task uuid
        self.ansible["summary"] = {}

        self.current_task_uuid = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )
        self.porcelain = Porcelain()
        self.ansible_events = self.get_option("ansible_events").split(",")

    def v2_playbook_on_start(self, playbook, **kwargs):

        self.ansible["playbook"]["basedir"] = playbook._basedir
        self.ansible["playbook"]["filename"] = playbook._file_name
        self.ansible["playbook"]["plays"] = playbook.get_plays()

        if "v2_playbook_on_start" in self.ansible_events:
            pass

    def v2_playbook_on_task_start(self, task, **kwargs):

        self.ansible["tasks"].append({
          "uuid": task._uuid,
          "path": task.get_path(),
          "role": task._role,
          "task": task.get_name(),
        })

        self.current_task_uuid = task._uuid

        if "v2_playbook_on_task_start" in self.ansible_events:
            pass

    def _runner_on(self, status, result):
        task_uuid = self.current_task_uuid
        self.ansible["results"][task_uuid] = {
            "uuid": task_uuid,
            "status": status,
            "host": result._host,
            "result": result._result,
            "task": result._task,
        }

    def v2_runner_on_ok(self, result, **kwargs):
        self._runner_on("ok", result)
        if "v2_runner_on_ok" in self.ansible_events:
            pass

    def v2_runner_on_skipped(self, result, **kwargs):
        self._runner_on("skipped", result)
        if "v2_runner_on_skipped" in self.ansible_events:
            pass

    def v2_runner_on_unreachable(self, result, **kwargs):
        self._runner_on("unreachable", result)
        if "v2_runner_on_unreachable" in self.ansible_events:
            pass

    def v2_runner_on_failed(self, result, **kwargs):
        self._runner_on("failed", result)
        if "v2_runner_on_failed" in self.ansible_events:
            pass

    def v2_playbook_on_stats(self, stats):

        _hosts = sorted(stats.processed.keys())
        for _host in _hosts:
            summary = stats.summarize(_host)
            host = str(_host)
            self.ansible["summary"][host] = summary

        #     print("====")
        #     print(str(summary))
        #     statsline = " ".join(
        #         "{!s}={!r}".format(key, val) for (key, val) in summary.items()
        #     )
        #     print(str(statsline))
        #     # stats.append(f"{_host} : {_statsline}")

        print = self._display.display

        print("==== PLAYBOOK ====")
        print(str(self.ansible["playbook"]))

        print("==== TASKS ====")
        for task in self.ansible["tasks"]:
          print(str(task))

        print("==== RESULTS ====")
        for result in self.ansible["results"]:
          print(str(result))
          print(str(self.ansible["results"][result]))

        print("==== SUMMARY ====")
        print(str(self.ansible["summary"]))

        if "v2_playbook_on_stats" in self.ansible_events:
            pass
