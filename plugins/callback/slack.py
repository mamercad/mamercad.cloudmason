# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
  author: Mark Mercado (@mamercad)
  name: mamercad.cloudmason.slack
  type: notification
  requirements:
    - Allow in configuration C(callbacks_enabled = mamercad.cloudmason.slack) in C([default]).
    - The C(requests) Python library.
  short_description: Sends play events to a Slack channel.
  description:
    - This is an ansible callback plugin that sends status updates to a Slack channel during playbook execution.
  options:
    slack_bot_token:
      description: Slack token; has the form C(xoxb-37809492...).
      required: true
      env:
        - name: SLACK_BOT_TOKEN
      ini:
        - section: callback_slack
          key: slack_bot_token
    slack_channel:
      description: Slack channel; has the form C(#bots).
      required: true
      env:
        - name: SLACK_CHANNEL
      ini:
        - section: callback_slack
          key: slack_channel
    slack_format:
      description: Textual display style.
      choices: ["plain", "fixed"]
      default: plain
      env:
        - name: SLACK_FORMAT
      ini:
        - section: callback_slack
          key: slack_format
    slack_cadence:
      description: Realtime or buffered.
      choice: ["realtime", "buffered"]
      default: realtime
      env:
        - name: SLACK_CADENCE
      ini:
        - section: callback_slack
          key: slack_cadence
    slack_threading:
      description: Use Slack threads (or not).
      default: false
      env:
        - name: SLACK_THREADING
      ini:
        - section: callback_slack
          key: slack_threading
    ansible_events:
      description: Ansible events for which to notify on.
      default: v2_playbook_on_start,v2_playbook_on_play_start,v2_playbook_on_task_start,v2_runner_on_ok,v2_runner_on_skipped,v2_runner_on_unreachable,v2_runner_on_failed,v2_playbook_on_stats
      env:
        - name: ANSIBLE_EVENTS
      ini:
        - section: callback_slack
          key: ansible_events
"""

import json
import yaml
import requests

from ansible.plugins.callback import CallbackBase
from ansible import constants as C

class Slack(object):
    def __init__(self, display, token, channel, threading):
        self.display = display
        self.token = token
        self.channel = channel
        self.threading = threading
        self.thread_ts = None

    def post_message(self, **kwargs):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-type": "application/json; charset=utf-8",
        }

        payload = {
            "channel": self.channel,
            **kwargs,
        }

        # if self.threading:
        #     payload.update({"thread_ts": self.thread_ts})

        slack = requests.post(
            "https://slack.com/api/chat.postMessage", headers=headers, json=payload
        )

        # if slack.status_code != requests.codes.ok:
        #     self._display.error(slack.text)
        # else:
        response = slack.json()
        # if response.get("ok", False) is not True:
        #     self.display.display(slack.text)
        # else:
        #     if self.slack_ts is None:
        #         self.slack_ts = response.get("ts", None)

class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "mamercad.cloudmason.slack"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.ansible = {}
        self.ansible["playbook"] = {}
        self.ansible["tasks"] = []
        self.ansible["results"] = {}
        self.ansible["summary"] = {}

        self.current_play_uuid = None
        self.current_play_name = None
        self.current_task_uuid = None
        self.current_task_name = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.slack_bot_token = self.get_option("slack_bot_token")
        self.slack_channel = self.get_option("slack_channel")
        self.slack_format = self.get_option("slack_format")
        self.slack_cadence = self.get_option("slack_cadence")
        self.slack_threading = self.get_option("slack_threading")
        self.ansible_events = self.get_option("ansible_events").split(",")

        self.slack_buffer = []

        self.slack = Slack(self._display, self.slack_bot_token, self.slack_channel, self.slack_threading)

        if self.slack_bot_token is None:
            self._display.warning(
                "Slack Bot Token was not provided; it "
                "can be provided using SLACK_BOT_TOKEN "
                "environment variable."
            )
            self.disabled = True

        if self.slack_channel is None:
            self._display.display(
                "Slack Channel was not provided; it "
                "can be provided using SLACK_CHANNEL "
                "environment variable."
            )
            self.disabled = True

    def _format(self, text, multline=True):
        if self.slack_format == "fixed":
            if multline:
                return(f"```{text}```")
            else:
                return(f"`{text}`")
        else:
            return(f"{text}")

    def v2_playbook_on_start(self, playbook, **kwargs):

        self.ansible["playbook"]["basedir"] = playbook._basedir
        self.ansible["playbook"]["filename"] = playbook._file_name
        self.ansible["playbook"]["plays"] = playbook.get_plays()

        if "v2_playbook_on_start" in self.ansible_events:
            plays = str(playbook.get_plays())[1:-1]
            basedir = playbook._basedir
            filename = playbook._file_name
            text="Starting playbook"
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Starting playbook :rocket:",
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"Directory: {basedir}\n"
                                f"Filename: {filename}\n"
                                f"Plays: {plays}\n"
                            )
                        }
                    ]
                }
            ]
            if self.slack_cadence == "realtime":
                self.slack.post_message(text=text, blocks=blocks)
            else:
                self.slack_buffer.append(blocks)

    def v2_playbook_on_play_start(self, play):
        self.play_uuid = str(play._uuid)
        self.play_name = str(play.name)

        self.current_play_uuid = self.play_uuid
        self.current_play_name = self.play_name

        if "v2_playbook_on_play_start" in self.ansible_events:
            text = self._format(f"PLAY [ {self.current_play_name} ]")
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{text}",
                    }
                }
            ]
            if self.slack_cadence == "realtime":
                self.slack.post_message(text=text, blocks=blocks)
            else:
                self.slack_buffer.append(blocks)

    def v2_playbook_on_task_start(self, task, **kwargs):

        self.ansible["tasks"].append({
          "uuid": task._uuid,
          "path": task.get_path(),
          "role": task._role,
          "task": task.get_name(),
        })

        self.current_task_uuid = task._uuid
        self.current_task_name = task.get_name()

        if "v2_playbook_on_task_start" in self.ansible_events:
            task_name = str(task.get_name())
            text = self._format(f"TASK [ {task_name} ]")
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{text}",
                    }
                }
            ]
            if self.slack_cadence == "realtime":
                self.slack.post_message(text=text, blocks=blocks)
            else:
                self.slack_buffer.append(blocks)

    def _runner_on(self, status, result):
        task_uuid = self.current_task_uuid
        self.ansible["results"][task_uuid] = {
            "uuid": task_uuid,
            "status": status,
            "host": result._host,
            "result": result._result,
            "task": result._task,
        }

        host = result._host
        changed = str(result._result["changed"]).lower()
        msg = str(result._result["msg"])

        text = self._format(f"{status}: [ {host} ] => changed={changed}")
        msg = self._format(msg)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{text}\n"
                        f"{msg}\n"
                    )
                }
            }
        ]
        if self.slack_cadence == "realtime":
            self.slack.post_message(text=text, blocks=blocks)
        else:
            self.slack_buffer.append(blocks)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self._runner_on("ok", result)
        if "v2_runner_on_ok" in self.ansible_events:
            pass

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self._runner_on("skipped", result)
        if "v2_runner_on_skipped" in self.ansible_events:
            pass

    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        self._runner_on("unreachable", result)
        if "v2_runner_on_unreachable" in self.ansible_events:
            pass

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self._runner_on("failed", result)
        if "v2_runner_on_failed" in self.ansible_events:
            pass

    def v2_playbook_on_stats(self, stats, *args, **kwargs):

        summaries = []
        _hosts = sorted(stats.processed.keys())
        for _host in _hosts:
            summary = stats.summarize(_host)
            host = str(_host)
            statsline = " ".join("{!s}={!r}".format(key, val) for (key, val) in summary.items())
            summaries.append({"host": host, "stats": statsline})

        summary_lines = "PLAY RECAP\n"
        for summary in summaries:
            summary_lines += summary["host"] + ": " + summary["stats"] + "\n"

        text = f"PLAY RECAP"
        summary_lines = self._format(summary_lines, multline=True)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{summary_lines}"
                }
            }
        ]
        if self.slack_cadence == "realtime":
            self.slack.post_message(text=text, blocks=blocks)
        else:
            self.slack_buffer.append(blocks)

        print = self._display.display
        blocks = []
        for b in self.slack_buffer:
            blocks.append(b[0])
        self.slack.post_message(blocks=blocks)

        if "v2_playbook_on_stats" in self.ansible_events:
            pass
