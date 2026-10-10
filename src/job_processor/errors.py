class Rejected(Exception):
    """The flight plan cannot be processed, and trying again will not help."""


class WeatherUnavailable(Exception):
    """The weather service did not give a usable answer. The job goes on without wind."""
