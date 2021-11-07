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
        - section: callback_slack
          key: slack_bot_token
    slack_channel:
      required: true
      description: Slack channel; has the form C(#bots).
      env:
        - name: SLACK_CHANNEL
      ini:
        - section: callback_slack
          key: slack_channel
    slack_ansible_events:
      required: false
      description: Ansible events for which to notify on.
      default: v2_playbook_on_start,v2_playbook_on_task_start,v2_playbook_on_play_start,v2_runner_on_ok,v2_runner_on_skipped,v2_runner_on_unreachable,v2_runner_on_failed,v2_playbook_on_stats
      env:
        - name: SLACK_ANSIBLE_EVENTS
      ini:
        - section: callback_slack
          key: slack_ansible_events
    slack_threading:
      required: false
      description: Use Slack threads (or not).
      default: false
      ini:
        - section: callback_slack
          key: slack_threading
"""

import json
import os
import yaml
import requests
from pprint import pprint

from ansible.plugins.callback import CallbackBase


class SlackHeader(object):
    def __init__(self, text, *args, **kwargs):
        self._block = {
            "type": "header",
            "text": {"type": "plain_text", "text": text, "emoji": True},
        }

    @property
    def block(self):
        return self._block


class SlackDivider(object):
    def __init__(self, *args, **kwargs):
        self._block = {"type": "divider"}

    @property
    def block(self):
        return self._block


class SlackContext(object):
    def __init__(self, text, type="mrkdwn", *args, **kwargs):
        self._block = {"type": "context", "elements": [{"type": type, "text": text}]}

    @property
    def block(self):
        return self._block


class SlackSection(object):
    def __init__(self, text, type="mrkdwn", fenced=False, *args, **kwargs):
        self._block = {"type": "section", "text": {"type": type, "text": text}}

    @property
    def block(self):
        return self._block


class SlackClient(object):
    def __init__(self, token, channel, threading=False, *args, **kwargs):
        self._token = token
        self._channel = channel
        self._threading = threading
        self._thread_ts = None
        self._text = None
        self._blocks = []

    def send(self, text="", blocks=[], *args, **kwargs):
        payload = {}

        if text or blocks:
            payload = {"channel": self._channel, "text": text, "blocks": blocks}
        elif self._text or self._blocks:
            payload = {
                "channel": self._channel,
                "text": self._text,
                "blocks": self._blocks,
            }

        if not payload:
            raise Exception("Missing text or blocks")

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-type": "application/json; charset=utf-8",
        }
        if self._threading:
            if self._slack_ts is not None:
                payload.update({"thread_ts": self._slack_ts})
        try:
            slack = requests.post(
                "https://slack.com/api/chat.postMessage", headers=headers, json=payload
            )
        except Exception:
            raise
        if slack.status_code != requests.codes.ok:
            raise Exception(f"Slack response code not ok [{slack.status_code}]")
        response_json = slack.json()
        response_text = slack.text
        response_ok = response_json.get("ok", False)
        if not response_ok:
            raise Exception(f"Slack response not ok [{response_ok}] [{response_text}]")
        response_ts = response_json.get("ts", None)
        if response_ts:
            self._slack_ts = response_ts

    def add(self, block, *args, **kwargs):
        self._blocks.append(block)


class OverallStats(object):
    def __init__(self):
        self._all = []
        self._passed = []
        self._failed = []

    @property
    def all(self):
        return self._all

    @property
    def passed(self):
        return self._passed

    @property
    def failed(self):
        return self._failed

    def set(self, host, status):
        if not host in self._all:
            self._all.append(host)

        if status == "passed":
            self._passed.append(host)

        if status == "failed":
            self._failed.append(host)

        if host in self._passed and status != "passed":
            self._passed.remove(host)

        if host in self._failed and status != "failed":
            self._failed.remove(host)

    @property
    def pct(self):
        if not len(self._all):
            return 0
        return 100 * len(self._passed) / len(self._all)


class PlayStats(object):
    def __init__(self):
        self._stats = {}

    @property
    def stats(self):
        return self._stats

    def set(self, host, task, status, result):
        if not host in self._stats:
            self._stats[host] = []
        self._stats[host].append({"task": task, "status": status, "result": result})

    def last(self, host):
        if host in self._stats:
            return self._stats[host][-1]
        return None


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "slack"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct
        )

        self.print = self._display

        self.slack_bot_token = self.get_option("slack_bot_token")
        self.slack_channel = self.get_option("slack_channel")
        self.slack_ansible_events = self.get_option("slack_ansible_events").split(",")
        self.slack_threading = self.get_option("slack_threading")

        if self.slack_bot_token is None:
            self.disabled = True
            self.print.warning(
                "Slack Bot Token was not provided; it"
                "can be provided using `SLACK_BOT_TOKEN`"
                "environment variable."
            )

        if self.slack_channel is None:
            self.disabled = True
            self.print.warning(
                "Slack Channel was not provided; it"
                "can be provided using `SLACK_CHANNEL`"
                "environment variable."
            )

        self.overall_stats = OverallStats()
        self.play_stats = PlayStats()
        self.slack = SlackClient(self.slack_bot_token, self.slack_channel)

    def v2_playbook_on_start(self, playbook, *args, **kwargs):
        self.playbook_basedir = playbook._basedir
        self.playbook_name = os.path.basename(playbook._file_name)
        self.plays = playbook.get_plays()

        self.print.v(f"playbook_basedir: {self.playbook_basedir}")
        self.print.v(f"playbook_name: {self.playbook_name}")
        self.print.v(f"plays: {str(self.plays)}")

        if "v2_playbook_on_start" in self.slack_ansible_events:
            message = (
                f"*v2_playbook_on_start*\n"
                f"playbook_basedir: {self.playbook_basedir}\n"
                f"playbook_name: {self.playbook_name}\n"
                f"plays: {self.plays}\n"
            )

        self.slack.add(SlackHeader(text=f"{self.playbook_name}").block)


    def v2_playbook_on_play_start(self, play, *args, **kwargs):
        self.play_name = play.get_name()
        self.play_roles = play.get_roles()
        self.play_tasks = play.get_tasks()
        self.play_uuid = play._uuid

        self.print.v(f"play_name: {self.play_name}")
        self.print.v(f"play_roles: {str(self.play_roles)}")
        self.print.v(f"play_tasks: {str(self.play_tasks)}")
        self.print.v(f"play_uuid: {self.play_uuid}")

        if "v2_playbook_on_play_start" in self.slack_ansible_events:
            message = (
                f"*v2_playbook_on_play_start*\n"
                f"play_name: {self.play_name}\n"
                f"play_roles: {self.play_roles}\n"
                f"play_tasks: {self.play_tasks}\n"
                f"play_uuid: {self.play_uuid}\n"
            )


    def v2_playbook_on_task_start(self, task, *args, **kwargs):
        self.role_name = task._role
        self.task_name = task.get_name()

        self.print.v(f"role_name: {self.role_name}")
        self.print.v(f"task_name: {self.task_name}")

        if "v2_playbook_on_task_start" in self.slack_ansible_events:
            message = f"*v2_playbook_on_task_start*\n" f"task_name: {self.task_name}\n"

    def _runner_on(self, status, result, *args, **kwargs):
        self.status = status
        self.host = str(result._host)
        self.result = result._result
        self.task = result._task
        self.task_name = result.task_name
        self.is_changed = result.is_changed()
        self.is_failed = result.is_failed()
        self.is_skipped = result.is_skipped()
        self.is_unreachable = result.is_unreachable()

        self.print.v(f"host: {self.host}")
        self.print.v(f"result: {self.result}")
        self.print.v(f"task: {self.task}")
        self.print.v(f"task_name: {self.task_name}")
        self.print.v(f"is_changed: {self.is_changed}")
        self.print.v(f"is_failed: {self.is_failed}")
        self.print.v(f"is_skipped: {self.is_skipped}")
        self.print.v(f"is_unreachable: {self.is_unreachable}")

        self.play_stats.set(self.host, self.task_name, self.status, self.result)

        if f"v2_runner_on_{status}" in self.slack_ansible_events:
            message = (
                f"*v2_runner_on_{status}*\n"
                f"host: {self.host}\n"
                f"task_name: {self.task_name}\n"
                f"result: {self.result}\n"
            )

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self._runner_on(status="ok", result=result)

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self._runner_on(status="skipped", result=result)

    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        self._runner_on(status="unreachable", result=result)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self._runner_on(status="failed", result=result)

    def v2_playbook_on_stats(self, stats, *args, **kwargs):
        hosts = sorted(stats.processed.keys())

        self.print.v(f"hosts: {str(hosts)}")

        for host in hosts:
            summary = stats.summarize(host)
            self.print.v(f"summarize {host}: {str(summary)}")

            if summary.get("failures") or summary.get("unreachable"):
                self.overall_stats.set(host, "failed")
                self.slack.add(SlackSection(text=f":large_red_square: *{host}* failed").block)
                if self.play_stats.last(host):
                    self.slack.add(SlackSection(text=f"```{json.dumps(self.play_stats.last(host), indent=4)}```").block)
            else:
                self.overall_stats.set(host, "passed")
                self.slack.add(SlackSection(text=f":large_green_square: *{host}* passed").block)

            if f"v2_playbook_on_stats" in self.slack_ansible_events:
                message = f"*v2_playbook_on_stats*\n" f"{host}: {str(summary)}\n"


        all = self.overall_stats.all
        passed = self.overall_stats.passed
        failed = self.overall_stats.failed
        pct = self.overall_stats.pct

        self.slack.add(SlackContext(
          text=(
            f"> Summary {len(all)} hosts"
            " • "
            f"{len(passed)*':large_green_square: '}"
            f"{len(passed)} passed"
            " • "
            f"{len(failed)*':large_red_square: '}"
            f"{len(failed)} failed"
            " • "
            f"{pct:.1f}% success\n"
          )).block
        )

        self.slack.send()
