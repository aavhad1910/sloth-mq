import time


class PerformanceTimer:

    def __init__(self):
        self._start_time = None
        self._elapsed = None
        self.name = None
        self.laps = list()

    def start(self, name):
        self._start_time = time.time()
        self.name = name

    def lap(self, name):
        if self.laps:
            self.end_lap()
        lap_instance = PerformanceTimer()
        lap_instance.start(name)
        self.laps.append(lap_instance)

    def end_lap(self):
        last_lap = self.laps[-1]
        if last_lap._elapsed:
            return
        last_lap.end()

    def elapsed(self, precision=4):
        return round(self._elapsed, precision)

    def end(self):
        if self.laps:
            self.end_lap()
        self._elapsed = time.time() - self._start_time

    def get_presentable(self):
        data = {
            'name': self.name,
            'elapsed_time': self.elapsed(),
        }
        if not self.laps:
            return data

        lap_data = {}
        for index, lap in enumerate(self.laps):
            lap_data[lap.name] = lap.get_presentable()

        data['laps'] = lap_data
        return data
