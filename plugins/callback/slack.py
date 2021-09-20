# -*- coding: utf-8 -*-
# (C) 2021, Mark Mercado <mamercad@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  author: Mark Mercado (@mamercad)
  name: slack
  type: notification
  requirements:
    - Allow in configuration C(callbacks_enabled = slack) in C([default]).
    - Specify the path in configuration C(callback_plugins = ./plugins/callback:/usr/share/ansible/plugins/callback).
    - The C(slack_sdk) Python library.
  short_description: Sends play events to a Slack channel.
  description:
    - This is an ansible callback plugin that sends status updates to a Slack channel during playbook execution.
  options:
    slack_bot_token:
      required: true
      desciption: Slack bot token; has the form C(xoxb-37809492...).
      env:
        - name: SLACK_BOT_TOKEN
      ini:
        - section: callback_slack
          key: bot_token
    slack_channel:
      required: true
      desciption: Slack channel; has the form C(#bots).
      env:
        - name: SLACK_CHANNEL
      ini:
        - section: callback_slack
          key: channel
"""


import json
import yaml
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


# from ansible import context
# from ansible.module_utils.common.text.converters import to_text
# from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "mamercad.cloudmason.slack"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

        self.slack_bot_token = self.get_option("slack_bot_token")
        self.slack_channel = self.get_option("slack_channel")

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

        self.client = WebClient(token=self.slack_bot_token)
        self.channel = self.slack_channel

    def post_message(self, **kwargs):
        try:
            self.client.chat_postMessage(channel=self.channel, **kwargs)
        except SlackApiError as e:
            assert e.response.get("ok", True) is False
            assert e.response.get("error", False)
            raise Exception(f"{e.response['error']}")

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
        self.post_message(text="playbook start", blocks=blocks)

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
        self.post_message(text="task start", blocks=blocks)

    def v2_runner_on_ok(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = result._host
        _text = f"ok: [{_host}] => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        self.post_message(text="runner ok", blocks=blocks)

    def v2_runner_on_skipped(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = result._host
        _text = f"skipping: [{_host}] => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        self.post_message(text="runner skipped", blocks=blocks)

    def v2_runner_on_failed(self, result, **kwargs):
        _result = json.loads(self._dump_results(result._result))
        _changed = str(_result.get("changed", False)).lower()
        del _result["changed"]
        _result = yaml.dump(_result, indent=2)
        _host = result._host
        _text = f"fatal: [{_host}] => changed={_changed}"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{_text}\n  {_result}```"},
            }
        ]
        self.post_message(text="runner failed", blocks=blocks)

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
        self.post_message(text="playbook start", blocks=blocks)
