# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from os import stat
from re import I

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
      choices: ["plain", "fixed", "visual"]
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
from pprint import pprint
import datetime

from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class Slack(object):
    def __init__(self, print, token, channel, threading):
        self.print = print
        self.token = token
        self.channel = channel
        self.threading = threading
        self.thread_ts = None

    def send(self, *args, **kwargs):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-type": "application/json; charset=utf-8",
        }

        payload = {
            "channel": self.channel,
            **kwargs,
        }

        if self.threading:
            payload.update({"thread_ts": self.thread_ts})

        slack = requests.post(
            "https://slack.com/api/chat.postMessage", headers=headers, json=payload
        )

        if slack.status_code != requests.codes.ok:
            self.print(slack.text, color=C.COLOR_ERROR)
        else:
            response = slack.json()
            if response.get("ok", False) is not True:
                self.print(slack.text, color=C.COLOR_ERROR)
            else:
                if self.thread_ts is None:
                    self.thread_ts = response.get("ts", None)
                self.print(f"Slack message sent ts={self.thread_ts}", C.COLOR_DEBUG)


class SlackMessages(object):
    def __init__(self, print, slack):
        self.print = print
        self.slack = slack
        self.messages = []

    def __str__(self):
        return str(self.messages)

    def push(self, message):
        self.messages.append(message)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self.messages):
            self.i += 1
            return self.messages[self.i - 1]
        raise StopIteration

    def send(self):
        blocks = []
        for message in self.messages:
            blocks.append(message.get_blocks())
        flatten_blocks = [item for sublist in blocks for item in sublist]
        # self.slack.send(text="hello world", blocks=flatten_blocks)
        # not sure what to use as text here
        self.slack.send(blocks=flatten_blocks)

class SlackMessage(object):
    def __init__(self, print, slack, text, context, divider=False, *args, **kwargs):
        self.print = print
        self.slack = slack
        self.text = text
        self.context = context
        self.divider = divider
        self.buffered = []

        self.blocks = []

        if divider:
            self.blocks.append(self._slack_divider())

        if text:
            self.blocks.append(self._slack_block_section())

        if context:
            self.blocks.append(self._slack_block_context())

        self.print(str(self.blocks), color=C.COLOR_ERROR)

    def _slack_text(self):
        pieces = []

        if "ts" in self.text:
            pieces.append(f"{self.text['ts']}")

        if "pre" in self.text:
            pieces.append(f"*{self.text['pre']}*")

        if "text" in self.text:
            pieces.append(f"[ {self.text['text']} ]")

        if "post" in self.text:
            pieces.append(f"⮕ {self.text['post']}")

        return(" ".join(pieces))

    def _slack_divider(self):
        return {
            "type": "divider",
        }

    def _slack_block_section(self):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": str(self._slack_text()),
            },
        }

    def _slack_block_context(self):
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{self.context['text']}",
                }
            ],
        }

    def send(self):
        self.print("SlackMessage send", color=C.COLOR_ERROR)
        self.slack.send(text=self._slack_text(), blocks=self.blocks)

    def get_blocks(self):
        return self.blocks


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
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

        self.slack_bot_token = self.get_option("slack_bot_token")
        self.slack_channel = self.get_option("slack_channel")
        self.slack_format = self.get_option("slack_format")
        self.slack_cadence = self.get_option("slack_cadence")
        self.slack_threading = self.get_option("slack_threading")
        self.ansible_events = self.get_option("ansible_events").split(",")

        self.slack = Slack(
            print=self._display.display,
            token=self.slack_bot_token,
            channel=self.slack_channel,
            threading=self.slack_threading,
        )

        self.slack_messages = SlackMessages(print=self._display.display, slack=self.slack)

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


    def _get_ts(self):
        now = datetime.datetime.now()
        return f"{now.hour:02d}:{now.minute:02d}"


    def v2_playbook_on_start(self, playbook, **kwargs):
        self._display.display("v2_playbook_on_start", color=C.COLOR_DEBUG)

        self.ansible["playbook"]["basedir"] = playbook._basedir
        self.ansible["playbook"]["filename"] = playbook._file_name
        self.ansible["playbook"]["plays"] = playbook.get_plays()

        if "v2_playbook_on_start" in self.ansible_events:
            plays = str(playbook.get_plays())[1:-1]
            basedir = playbook._basedir
            filename = playbook._file_name

            text = {
                "ts": self._get_ts(),
                "pre": "PLAYBOOK",
                "text": "Starting playbook",
                "post": ":rocket:",
            }
            context = {
                "text": (
                    f"Directory: {basedir}\n"
                    f"Filename: {filename}\n"
                    f"Plays: {plays}\n"
                )
            }

            message = SlackMessage(
                print=self._display.display,
                slack=self.slack,
                text=text,
                context=context,
                divider=True,
            )

            if self.slack_cadence == "realtime":
                message.send()
            else:
                self.slack_messages.push(message)

    def v2_playbook_on_play_start(self, play):
        self._display.display("v2_playbook_on_play_start", color=C.COLOR_DEBUG)
        self.play_uuid = str(play._uuid)
        self.play_name = str(play.name)

        self.current_play_uuid = self.play_uuid
        self.current_play_name = self.play_name

        if "v2_playbook_on_play_start" in self.ansible_events:
            text = {
                "ts": self._get_ts(),
                "pre": "PLAY",
                "text": self.play_name,
                "post": "",
            }

            message = SlackMessage(
                print=self._display.display, slack=self.slack, text=text, context={}
            )

            if self.slack_cadence == "realtime":
                message.send()
            else:
                self.slack_messages.push(message)

    def v2_playbook_on_task_start(self, task, **kwargs):
        self._display.display("v2_playbook_on_task_start", color=C.COLOR_DEBUG)

        self.ansible["tasks"].append(
            {
                "uuid": task._uuid,
                "path": task.get_path(),
                "role": task._role,
                "task": task.get_name(),
            }
        )

        self.current_task_uuid = task._uuid
        self.current_task_name = task.get_name()

        if "v2_playbook_on_task_start" in self.ansible_events:
            task_name = str(task.get_name())
            text = {
                "ts": self._get_ts(),
                "pre": "TASK",
                "text": task_name,
                "post": "",
            }

            message = SlackMessage(
                print=self._display.display, slack=self.slack, text=text, context={}
            )

            if self.slack_cadence == "realtime":
                message.send()
            else:
                self.slack_messages.push(message)

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

        print = self._display.display
        print(str(status), color=C.COLOR_ERROR)
        print(str(result._result), color=C.COLOR_ERROR)

        key = None

        if "msg" in result._result.keys():
            key = "msg"
        else:
            # hrm the "first key", definitely not sure about this
            key = list(result._result.keys())[0]

        msg = str(result._result[key]).strip()

        changed = result._result.get("changed")
        if changed is None:
            post = ""
        else:
            post = f"changed={str(changed).lower()}"


        if status == "ok":
            post += " ⮕ :ballot_box_with_check:"
        if status == "failed":
            post += " ⮕ :skull:"

        text = {
            "ts": self._get_ts(),
            "pre": status,
            "text": host,
            "post": post,
        }
        context = {
            "text": f"```{key}: {msg}```",
        }

        message = SlackMessage(
            print=self._display.display, slack=self.slack, text=text, context=context
        )

        if self.slack_cadence == "realtime":
            message.send()
        else:
            self.slack_messages.push(message)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self._display.display("v2_runner_on_ok", color=C.COLOR_DEBUG)
        if "v2_runner_on_ok" in self.ansible_events:
            self._runner_on("ok", result)

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self._display.display("v2_runner_on_skipped", color=C.COLOR_DEBUG)
        if "v2_runner_on_skipped" in self.ansible_events:
            self._runner_on("skipped", result)

    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        self._display.display("v2_runner_on_unreachable", color=C.COLOR_DEBUG)
        if "v2_runner_on_unreachable" in self.ansible_events:
            self._runner_on("unreachable", result)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self._display.display("v2_runner_on_failed", color=C.COLOR_DEBUG)
        if "v2_runner_on_failed" in self.ansible_events:
            self._runner_on("failed", result)

    def v2_playbook_on_stats(self, stats, *args, **kwargs):
        self._display.display("v2_runner_on_stats", color=C.COLOR_DEBUG)
        if "v2_playbook_on_stats" in self.ansible_events:

            summaries = []
            _hosts = sorted(stats.processed.keys())
            for _host in _hosts:
                summary = stats.summarize(_host)
                host = str(_host)
                statsline = " ".join(
                    "{!s}={!r}".format(key, val) for (key, val) in summary.items()
                )
                summaries.append({"host": host, "stats": statsline})

            summary_lines = ""
            for summary in summaries:
                summary_lines += summary["host"] + ": " + summary["stats"] + "\n"

            text = {
                "ts": self._get_ts(),
                "pre": f"PLAY RECAP",
            }
            context = {
                "text": f"```{summary_lines}```",
            }

            message = SlackMessage(
                print=self._display.display, slack=self.slack, text=text, context=context
            )

            if self.slack_cadence == "realtime":
                message.send()
            else:
                self.slack_messages.push(message)

            self.slack_messages.send()
