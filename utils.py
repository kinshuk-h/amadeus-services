import isodate
import requests

from bs4 import BeautifulSoup

OFFER_SORT_KEYS = {
    "price-wise": lambda f: float(f["price"]["grandTotal"]),
    "duration-wise": lambda f: (
        isodate.parse_duration(f["itineraries"][0]["duration"]).total_seconds(),
        isodate.parse_duration(f["itineraries"][1]["duration"]).total_seconds() if len(f["itineraries"]) > 1 else 0,
        float(f["price"]["grandTotal"])
    ),
    "air-india": lambda f: (
        1 if any(segment["carrierCode"]=="AI" for segment in f["itineraries"][0]["segments"]) else 2,
        1 if len(f["itineraries"]) > 1 and \
            any(segment["carrierCode"]=="AI" for segment in f["itineraries"][1]["segments"]) else 2,
        float(f["price"]["grandTotal"])
    ),
    "stop-count": lambda f: (
        len(f["itineraries"][0]["segments"]),
        len(f["itineraries"][1]["segments"]) if len(f["itineraries"]) > 1 else 0,
        float(f["price"]["grandTotal"])
    ),
}

OFFER_SORT_KEY_NAMES = {
    "price-wise-asc"    : "Fare - Low to High",
    "price-wise-desc"   : "Fare - High to Low",
    "duration-wise-asc" : "Duration - Shorter to Longer",
    "duration-wise-desc": "Duration - Longer to Shorter",
    "stop-count-asc"    : "Number of Stops - Low to High",
    "stop-count-desc"   : "Number of Stops - High to Low",
    "air-india-asc"     : "Air India Flights as a carrier",
    "air-india-desc"    : "Without Air India Flights as a carrier",
}

def get_airport_codes(query):
    response = requests.get("https://www.iata.org/en/publications/directories/code-search/",
        params = { "airport.search": query }
    )
    response.raise_for_status()
    page = BeautifulSoup(response.text)
    results = []
    if tbody := page.select_one("div.airportcodessearchblock table.datatable tbody"):
        for row in tbody("tr"):
            cells = row("td")
            results.append({
                "city"   : cells[0].text,
                "airport": cells[1].text,
                "code"   : cells[2].text
            })
    return results

class Duration:
    """ Class to format a duration in seconds. """
    def __init__(self, seconds = 0):
        time = seconds or 0
        self.seconds = time % 60; time //= 60
        self.minutes = time % 60; time //= 60
        self.hours   = time % 24; time //= 24
        self.days    = time
    def __str__(self) -> str:
        return f"{self.days:02}:{self.hours:02}:{self.minutes:02}:{self.seconds:02}"
    def __repr__(self) -> str:
        return f"Duration(seconds = {self.days * 86400 + self.hours * 3600 + self.minutes * 60 + self.seconds})"
    def text(self, use_punctuation = False):
        text_str = ""
        p = ', ' if use_punctuation else ' '
        if self.days   : text_str += f"{                       self.days   } day{'s' if self.days    != 1 else ''}"
        if self.hours  : text_str += f"{p if text_str else ''}{self.hours  } hr{ 's' if self.hours   != 1 else ''}"
        if self.minutes: text_str += f"{p if text_str else ''}{self.minutes} min{'s' if self.minutes != 1 else ''}"
        if self.seconds: text_str += f"{p if text_str else ''}{self.seconds} sec{'s' if self.seconds != 1 else ''}"
        return ' & '.join(text_str.rsplit(", ", 1)) or "Unknown"
    def __format__(self, format_spec: str) -> str:
        if not format_spec: return self.__str__()
        result = format_spec.replace("%%", "%")
        result = result.replace("%T", self.text(use_punctuation = True))
        result = result.replace("%t", self.text())
        result = result.replace("%r", self.__repr__())
        result = result.replace("%d", f"{self.days:02}")
        result = result.replace("%h", f"{self.hours:02}")
        result = result.replace("%m", f"{self.minutes:02}")
        result = result.replace("%s", f"{self.seconds:02}")
        result = result.replace("%D", f"{self.days}d" if self.days else '')
        result = result.replace("%H", f"{self.hours}h" if self.hours else '')
        result = result.replace("%M", f"{self.minutes}m" if self.minutes else '')
        result = result.replace("%s", f"{self.seconds}s" if self.seconds else '')
        return result