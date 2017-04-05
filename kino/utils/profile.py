
import datetime

import utils

class Profile(object):

    def __init__(self):
        profile = utils.Config().profile
        self.schedule = profile['schedule']
        self.location = profile['location']
        self.task = profile['task']
        self.score = profile['score']

    def get_schedule(self, keyword, parsed=False):
        if parsed:
            return self.__parse_during_time(self.schedule[keyword])
        else:
            return self.schedule[keyword]

    def __parse_during_time(self, during_text):
        start_time, end_time = during_text.split("~")
        return (self.__parse_time(start_time), self.__parse_time(end_time))

    def __parse_time(self, time_text):
        hour, minute = time_text.split(":")
        return ( int(hour), int(minute) )

    def get_location(self, station=False):
        start_time, end_time = self.get_working_hour_time(parsed=True)
        start_h, start_m = start_time
        end_h, end_m = end_time

        now = datetime.datetime.now()
        start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

        if (start <= now <= end):
            if station:
                return self.location['WORK_PLACE_STATION_NAME']
            else:
                return self.location['WORK_PLACE']
        else:
            if station:
                return self.location['HOME_STATION_NAME']
            else:
                return self.location['HOME']

    def get_task(self, keyword):
        return self.task[keyword]

    def get_score(self, keyword):
        return self.score[keyword]
