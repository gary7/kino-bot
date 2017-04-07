import arrow
import datetime
from dateutil import tz


class ArrowUtil(object):

    def __init__(self):
        pass

    def get_action_time(self, time):
        time_str = time.strip().replace('at', '')
        if time_str == "now":
            return arrow.get(arrow.now(), tzinfo=tz.tzlocal())
        else:
            return arrow.get(
                time_str,
                'MMMM D, YYYY  hh:mma',
                tzinfo=tz.tzlocal())

    def get_curr_time_diff(self, start=None, stop=None, base_hour=False):
        if isinstance(start, str):
            start = arrow.get(start)
        if isinstance(stop, str):
            stop = arrow.get(stop)

        if stop is None:
            stop = arrow.utcnow()

        diff = (stop - start).seconds / 60
        if base_hour:
            return round(diff / 60 * 100) / 100
        else:
            return int(diff)

    def is_between(self, start_time, end_time, now=None):
        if now is None:
            now = datetime.datetime.now()

        start_h, start_m = start_time
        end_h, end_m = end_time

        if end_h == 24 and end_m == 0:
            end_h = 23
            end_m = 59

        start = now.replace(
            hour=start_h,
            minute=start_m,
            second=0,
            microsecond=0)
        end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        if (start < now < end):
            return True
        else:
            return False

    def is_weekday(self):
        t = arrow.now()
        day_of_week = t.weekday()
        if day_of_week < 5:
            return True
        else:
            return False
