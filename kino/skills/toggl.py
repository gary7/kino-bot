
import arrow
from hbconfig import Config

from ..open_api.toggl import Toggl

from ..slack.resource import MsgResource
from ..slack.slackbot import SlackerAdapter

from ..skills.question import AttentionQuestion
from ..skills.todoist import TodoistManager

from ..utils.arrow import ArrowUtil
from ..utils.data_handler import DataHandler
from ..utils.logger import Logger
from ..utils.score import Score
from ..utils.state import State


class TogglManager(object):

    def __init__(self, slackbot=None):
        self.logger = Logger().get_logger()

        self.toggl = Toggl()
        self.toggl.setAPIKey(Config.open_api.toggl.TOKEN)

        wid = self.toggl.getWorkspace(
            name=Config.open_api.toggl.WORKSPACE_NAME)['id']
        self.toggl.setWorkspaceId(wid)

        if slackbot is None:
            self.slackbot = SlackerAdapter(channel=Config.slack.channel.get('TASK', '#general'))
        else:
            self.slackbot = slackbot

    def timer(self, description=None, doing=True, done=True):
        state = State()
        state.check()

        advice_rest_time = state.current.get(state.REST, {}).get('time', None)
        if advice_rest_time is not None:
            advice_rest_time = arrow.get(advice_rest_time)
            if advice_rest_time > arrow.now():
                self.slackbot.send_message(
                    text=MsgResource.TOGGL_ADVICE_REST(
                        time=advice_rest_time.format('HH:mm')))
                return

        current_timer = self.toggl.currentRunningTimeEntry()['data']
        if current_timer is None and doing == False:
            self.slackbot.send_message(text=MsgResource.TOGGL_ALREADY_BREAK)
            return

        if current_timer is None:
            if description is None or description == "":
                pid = None
            else:
                # matching name
                lower_description = description.lower()

                TOGGL_DELIMEITER = " - "
                if TOGGL_DELIMEITER in lower_description:
                    name = lower_description.split(" - ")[0]
                    pid = self.__get_pid(name=name)
                else:
                    pid = None

            self.toggl.startTimeEntry(description=description, pid=pid)
            self.slackbot.send_message(text=MsgResource.TOGGL_START)
        else:
            if (doing, done) == (True, False):
                self.slackbot.send_message(
                    text=MsgResource.TOGGL_ALREADY_DOING)
                return

            stop = self.toggl.stopTimeEntry(current_timer['id'])
            description = stop['data'].get('description', 'no description')
            diff_min = ArrowUtil.get_curr_time_diff(
                start=stop['data']['start'], stop=stop['data']['stop'])

            self.slackbot.send_message(text=MsgResource.TOGGL_STOP)
            self.slackbot.send_message(
                text=MsgResource.TOGGL_STOP_SUMMARY(
                    description=description, diff_min=diff_min))

            if done:
                todoist = TodoistManager()
                todoist.complete_by_toggl(description, int(diff_min))

            state.advice_rest(diff_min)

            if diff_min > 40:
                attention = AttentionQuestion()
                attention.question()

    def __get_pid(self, name=None):
        project = self.toggl.getWorkspaceProject(name=name.title())
        if project is None:
            pid = None
        else:
            pid = project['id']
        return pid

    def check_toggl_timer(self):
        current_timer = self.toggl.currentRunningTimeEntry()['data']
        self.logger.info(str(current_timer))
        if current_timer is None:
            return

        diff_min = ArrowUtil.get_curr_time_diff(
            start=current_timer['start'])
        self.logger.info("diff_min: " + str(diff_min))
        diff_min_divide_10 = int(diff_min / 10)
        if diff_min > 100:
            self.slackbot.send_message(text=MsgResource.TOGGL_NOTI_RELAY)
        else:
            for i in range(3, 10, 3):
                if diff_min_divide_10 == i:
                    self.slackbot.send_message(
                        text=MsgResource.TOGGL_TIMER_CHECK(diff_min=diff_min))
                    break

    def report(self, kind="chart", timely="weekly"):

        now = arrow.now()

        if timely == "daily":
            before_days = now.replace(days=0)
        elif timely == "weekly":
            before_days = now.replace(days=-6)

        data = {
            'since': before_days.format('YYYY-MM-DD'),
            'until': now.format('YYYY-MM-DD'),
            'calculate': 'time'
        }

        channel = Config.slack.channel.get('REPORT', '#general')

        if kind == "basic":
            f_name = "basic-report.pdf"
            self.toggl.getWeeklyReportPDF(data, f_name)
            self.slackbot.file_upload(
                f_name,
                channel=channel,
                title=timely + " 기본 리포트",
                comment=MsgResource.TOGGL_REPORT)
        elif kind == "chart":
            f_name = "chart-report.pdf"
            self.toggl.getSummaryReportPDF(data, f_name)
            self.slackbot.file_upload(
                f_name,
                channel=channel,
                title=timely + " 차트 리포트",
                comment=MsgResource.TOGGL_REPORT)
        elif kind == "detail":
            f_name = "detail-report.pdf"
            self.toggl.getDetailedReportPDF(data, f_name)
            self.slackbot.file_upload(
                f_name,
                channel=channel,
                title=timely + " 상세 리포트",
                comment=MsgResource.TOGGL_REPORT)

    def get_point(self):
        now = arrow.now()
        data = {
            'since': now.format('YYYY-MM-DD'),
            'until': now.format('YYYY-MM-DD'),
            'calculate': 'time'
        }

        today = self.toggl.getDetailedReport(data)
        if today['total_grand']:
            total_hours = round(today['total_grand'] / 60 / 60 / 10)
        else:
            total_hours = 0
        return Score.percent(total_hours, 100, 800)
