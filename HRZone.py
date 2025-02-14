from units import HR_ZONES

class HRZone:
    def __init__(self, title, zone):
        self.title = title
        assert zone in HR_ZONES, f'Zone must be one of the following: {HR_ZONES}'
        self.zone = zone

    def __eq__(self, other):
        return self.zone == other.zone

    def __str__(self):
        return self.title

    def __lt__(self, other):
        return self.zone < other.zone

    def __gt__(self, other):
        return self.zone > other.zone

    def __le__(self, other):
        return self.zone <= other.zone

    def __ge__(self, other):
        return self.zone >= other.zone

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.zone)

    def __repr__(self):
        return f'{self.title} | {self.zone}'
