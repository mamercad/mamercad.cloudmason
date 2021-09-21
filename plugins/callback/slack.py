# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from re import I

__metaclass__ = type

DOCUMENTATION = """
  author: Mark Mercado (@mamercad)
  name: slack
  type: notification
  requirements:
    - Allow in configuration C(callbacks_enabled = slack) in C([default]).
    - The C(requests) Python library.
  short_description: Sends play events to a Slack channel.
  description:
    - This is an ansible callback plugin that sends status updates to a Slack channel during playbook execution.
  options:
    slack_bot_token:
      required: true
      description: Slack token; has the form C(xoxb-37809492...).
      env:
        - name: SLACK_BOT_TOKEN
      ini:
        - section: callback_summary
          key: slack_bot_token
    slack_channel:
      required: true
      description: Slack channel; has the form C(#bots).
      env:
        - name: SLACK_CHANNEL
      ini:
        - section: callback_summary
          key: slack_channel
    ansible_events:
      required: false
      description: Ansible events for which to notify on.
      default: v2_playbook_on_start,v2_playbook_on_task_start,v2_runner_on_ok,v2_runner_on_skipped,v2_runner_on_unreachable,v2_runner_on_failed,v2_playbook_on_stats
      env:
        - name: ANSIBLE_EVENTS
      ini:
        - section: callback_summary
          key: ansible_events
    slack_threading:
      required: false
      description: Use Slack threads (or not).
      default: false
      ini:
        - section: callback_summary
          key: slack_threading
"""

import json
import yaml
import requests

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "mamercad.cloudmason.slack"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)

        self.slack_ts = None

        self.overall_summary = {}
        self.current_plays = None
        self.current_task = None

        #  overall_summary = {
        #    'host1' = [
        #       { 'task1' = 'ok' },
        #       { 'task2' = 'failed' },
        #    ],
        #    'host2' = [
        #       { 'task1' = 'ok' },
        #       { 'task2' = 'ok' },
        #       { 'task3' = 'failed' },
        #    ],
        #    'host3' = [
        #       { 'task1' = 'skipped' },
        #       { 'task2' = 'skipped' },
        #       { 'task3' = 'failed' },
        #    ],
        #    'host4' = [
        #       { 'task1' = 'skipped' },
        #       { 'task2' = ['ok', '...'] },
        #       { 'task3' = 'ok' },
        #    ],
        #    ...
        #  }

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

        self.slack_bot_token = self.get_option("slack_bot_token")
        self.slack_channel = self.get_option("slack_channel")
        self.ansible_events = self.get_option("ansible_events").split(",")
        self.slack_threading = self.get_option("slack_threading")

        if self.slack_bot_token is None:
            self.disabled = True
            self._display.warning(
                "Slack Bot Token was not provided; it"
                "can be provided using `SLACK_BOT_TOKEN`"
                "environment variable."
            )

        if self.slack_channel is None:
            self.disabled = True
            self._display.warning(
                "Slack Channel was not provided; it"
                "can be provided using `SLACK_CHANNEL`"
                "environment variable."
            )

    def post_message(self, **kwargs):
        try:
            headers = {
                "Authorization": f"Bearer {self.slack_bot_token}",
                "Content-type": "application/json; charset=utf-8",
            }

            payload = {
                "channel": self.slack_channel,
                **kwargs,
            }

            if self.slack_threading:
                if self.slack_ts is not None:
                    payload.update({"thread_ts": self.slack_ts})

            slack = requests.post(
                "https://slack.com/api/chat.postMessage", headers=headers, json=payload
            )

            if slack.status_code != requests.codes.ok:
                self._display.error(slack.text)
            else:
                resp = slack.json()
                if resp.get("ok", False) is not True:
                    self._display.error(slack.text)
                else:
                    if self.slack_ts is None:
                        self.slack_ts = resp.get("ts", None)

        except Exception as e:
            self._display.error(str(e))

    def v2_playbook_on_start(self, playbook, **kwargs):
        _plays = playbook.get_plays()
        _msg = f"PLAY {_plays}"
        _text = "{0} {1}".format(_msg, "*" * (79 - len(_msg)))
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{_text}```",
                },
            }
        ]
        if "v2_playbook_on_start" in self.ansible_events:
            self.post_message(text="playbook start", blocks=blocks)

        self.current_plays = str(_plays)

    def v2_playbook_on_task_start(self, task, **kwargs):
        _task_name = task.name
        _msg = f"TASK [{_task_name}]"
        _text = "{0} {1}".format(_msg, "*" * (79 - len(_msg)))
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{_text}```",
                },
            }
        ]
        if "v2_playbook_on_task_start" in self.ansible_events:
            self.post_message(text="task start", blocks=blocks)

        self.current_task = _task_name

    def v2_runner_on_ok(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = str(result._host)
        _text = f"ok: [{_host}] => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        if "v2_runner_on_ok" in self.ansible_events:
            self.post_message(text="runner ok", blocks=blocks)

        if _host not in self.overall_summary:
            self.overall_summary[_host] = []
        self.overall_summary[_host].append({self.current_task: ["ok", _result]})

    def v2_runner_on_skipped(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = str(result._host)
        _text = f"skipping: [{_host}] => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        if "v2_runner_on_skipped" in self.ansible_events:
            self.post_message(text="runner skipped", blocks=blocks)

        if _host not in self.overall_summary:
            self.overall_summary[_host] = []
        self.overall_summary[_host].append({self.current_task: ["skipped", _result]})

    def v2_runner_on_unreachable(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = str(result._host)
        _text = f"fatal: [{_host}]: UNREACHABLE! => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        if "v2_runner_on_unreachable" in self.ansible_events:
            self.post_message(text="runner unreachable", blocks=blocks)

        if _host not in self.overall_summary:
            self.overall_summary[_host] = []
        self.overall_summary[_host].append({self.current_task: ["unreachable", _result]})

    def v2_runner_on_failed(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = str(result._host)
        _text = f"fatal: [{_host}] => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        if "v2_runner_on_failed" in self.ansible_events:
            self.post_message(text="runner failed", blocks=blocks)

        if _host not in self.overall_summary:
            self.overall_summary[_host] = []
        self.overall_summary[_host].append({self.current_task: ["failed", _result]})

    def v2_playbook_on_stats(self, stats):
        _hosts = sorted(stats.processed.keys())
        _stats = []
        for _host in _hosts:
            summary = stats.summarize(_host)
            _statsline = " ".join(
                "{!s}={!r}".format(key, val) for (key, val) in summary.items()
            )
            _stats.append(f"{_host} : {_statsline}")

        _text = f"PLAY RECAP"
        _msg = "{0} {1}".format(_text, "*" * (79 - len(_text)))
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "```{0}\n{1}```".format(_msg, "\n".join(_stats)),
                },
            }
        ]
        if "v2_playbook_on_stats" in self.ansible_events:
            self.post_message(text="stats", blocks=blocks)

        self.display_overall_summary()

    def display_overall_summary(self):
        max_hostname_length = 0
        for host in sorted(self.overall_summary.keys()):
            if len(host) > max_hostname_length:
                max_hostname_length = len(host)

        max_taskname_length = 0
        for host in sorted(self.overall_summary.keys()):
            for task in self.overall_summary[host]:
                for k, v in task.items():
                    if len(k) > max_taskname_length:
                        max_taskname_length = len(k)

        max_failmsg_length = 0
        for host in sorted(self.overall_summary.keys()):
            last_task = self.overall_summary[host][-1]
            for k, v in last_task.items():
                if len(last_task[k][1]) > max_failmsg_length:
                    max_failmsg_length = len(last_task[k][1])

        _msgs = []
        _msgs.append(self.current_plays)
        for host in sorted(self.overall_summary.keys()):
            last_task = self.overall_summary[host][-1]
            for k, v in last_task.items():
                if last_task[k][0] in ["failed", "unreachable"]:
                    _msgs.append(f"{host.ljust(max_hostname_length, ' ')} | "
                                 f"failed | {k.ljust(max_taskname_length, ' ')} | "
                                 f"{last_task[k][1][:20]}")
                else:
                    _msgs.append(f"{host.ljust(max_hostname_length, ' ')} | passed")

        _msg = "\n".join(_msgs)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{_msg}```",
                },
            }
        ]
        self.post_message(text="overall summary", blocks=blocks)
