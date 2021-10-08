# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
  author: Mark Mercado (@mamercad)
  name: template
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
from ansible import constants as C


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "template"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.print = self._display.display
        self.verbosity = self._display.verbosity


    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

    def _all_vars(self, host=None, task=None):
        # host and task need to be specified in case 'magic variables' (host vars, group vars, etc)
        # need to be loaded as well
        return self._play.get_variable_manager().get_vars(
            play=self._play,
            host=host,
            task=task
        )

    def v2_playbook_on_start(self, playbook, **kwargs):
        self.playbook = playbook
        self.playbook_file_name = playbook._file_name


    def v2_playbook_on_play_start(self, play):
        self.play = play
        self.vm = play.get_variable_manager()
        self.extra_vars = self.vm.extra_vars
        self.play_vars = self.vm.get_vars(self.play)
        self.hostvars = self.vm.get_vars()['hostvars']

        # name = play.get_name().strip()
        # if not name:
        #     msg = u"play"
        # else:
        #     msg = u"PLAY [%s]" % name

        # self._play = play

        # self._display.banner(msg)
        # self._play = play

        # self._host_total = len(self._all_vars()['vars']['ansible_play_hosts_all'])
        # self._task_total = len(self._play.get_tasks()[0])
        # # self.print(str(self._all_vars()), color=C.COLOR_ERROR)
        # # self.print(str(self._all_vars()['vars']), color=C.COLOR_ERROR)
        # self.print(str(pprint(self._all_vars()['vars'])), color=C.COLOR_ERROR)

    def v2_playbook_on_include(self, included_file):
        self.included_file = included_file

    def v2_playbook_on_task_start(self, task, **kwargs):
        self.task = task

    def _runner_on(self, status, result):
        pass

    def v2_runner_on_ok(self, result, **kwargs):
        # host_vars = self.vm.get_vars()['hostvars'][result._host.name]
        # self._display.display(pprint(str(host_vars)))
        pass

    def v2_runner_on_skipped(self, result, **kwargs):
        pass

    def v2_runner_on_unreachable(self, result, **kwargs):
        pass

    def v2_runner_on_failed(self, result, **kwargs):
        pass

    def v2_playbook_on_stats(self, stats):
        pass
        self.print("============== extra_vars ===============================")
        self.print(str(self.extra_vars))
        self.print("============== play_vars ===============================")
        self.print(str(self.play_vars))
        self.print("============== hostvars ===============================")
        self.print(str(self.hostvars))

        self.print("=======================================================")
        if "xxx" in self.extra_vars:
            self.print(f"extra_vars {self.extra_vars['xxx']}")
        elif "xxx" in self.play_vars:
            self.print(f"play_vars {self.play_vars['xxx']}")
        else:
            self.print("no")
