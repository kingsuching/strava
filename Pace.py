import units
import json

class Pace:
    def __init__(self, min, sec=0, unit=units.MILES):
        assert type(min) == int and type(sec) == int, f"min and sec must be integers. Got {min} and {sec}"
        self.min = abs(min)
        self.sec = abs(sec)
        self.time = min*60 + sec
        self.unit = unit
        if self.unit not in [units.MILES, units.KILOMETERS]:
            raise ValueError(f"Unit must be miles or kilometers. Got {unit}")

    def __str__(self):
        return f"{self.min}:{self.sec:02}/{self.unit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.min == other.min and self.sec == other.sec and self.unit == other.unit

    def __lt__(self, other):
        return self.time > other.time

    def __le__(self, other):
        return self.time >= other.time

    def __gt__(self, other):
        return self.time < other.time

    def __ge__(self, other):
        return self.time <= other.time

    def __add__(self, other):
        if self.unit != other.unit:
            raise ValueError("Cannot add Paces with different units")
        sumTime = self.time + other.time
        sumMin = int(sumTime // 60)
        sumSec = int(sumTime % 60)
        pace = Pace(sumMin, sumSec, self.unit)
        return pace

    def __radd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)

    def __sub__(self, other):
        if self.unit != other.unit:
            raise ValueError("Cannot subtract Paces with different units")
        diffTime = self.time - other.time
        diffMin = int(diffTime // 60)
        diffSec = int(diffTime % 60)
        pace = Pace(diffMin, diffSec, self.unit)
        return pace

    def __truediv__(self, other):
        avgTime = self.time / other
        avgMin = int(avgTime // 60)
        avgSec = int(avgTime % 60)
        return Pace(avgMin, avgSec, self.unit)

    def __float__(self):
        return float(self.time)

    def __neg__(self):
        return Pace.fromSeconds(-self.time, self.unit)

    def __ne__(self, other):
        return not self == other

    def convert(self):
        if self.unit == units.MILES:
            newTime = self.time / units.FACTOR
            newMin = int(newTime // 60)
            newSec = int(newTime % 60)
            return Pace(newMin, newSec, units.KILOMETERS)
        else:
            newTime = self.time * units.FACTOR
            newMin = int(newTime // 60)
            newSec = int(newTime % 60)
            return Pace(newMin, newSec, units.MILES)

    @classmethod
    def from_mps(cls, speed_in_mps):
        """
        Create a Pace object from speed in meters per second (m/s).
        """
        if speed_in_mps == 0:
            return Pace(0, 0, units.MILES)
        if speed_in_mps < 0:
            return Pace.from_mps(-speed_in_mps)

        # Convert m/s to min/mi
        time_in_seconds = (1 / speed_in_mps) * 1609.344
        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds % 60)

        return Pace(minutes, seconds, units.MILES)

    @classmethod
    def fromSeconds(cls, time_in_seconds, unit=units.MILES):
        """
        Create a Pace object from time in seconds per [unit].
        """
        if time_in_seconds <= 0:
            return Pace(0, 0, unit)

        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds % 60)
        return Pace(minutes, seconds, unit)

    @classmethod
    def mean(cls, listOfPaces):
        return sum(listOfPaces)/len(listOfPaces)

    @classmethod
    def fromString(cls, paceStr):
        slashIndex = paceStr.index('/')
        colonIndex = paceStr.index(':')
        pieces = paceStr.split('/')
        assert colonIndex >= 1 and slashIndex >= 1, f"{paceStr} invalid"
        time = pieces[0]
        unit = pieces[1]
        min = int(time[:colonIndex])
        sec = int(time[colonIndex+1:])
        return Pace(min, sec, unit)

    def to_dict(self):
        return {
            'min': self.min,
            'sec': self.sec,
            'unit': self.unit,
            'time': self.time
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data):
        return Pace(data['min'], data['sec'], data['unit'])

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Pace.from_dict(data)