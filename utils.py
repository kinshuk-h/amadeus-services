import requests

from bs4 import BeautifulSoup

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

def unique_objects(objects):
    """ Returns unique dictionary objects from a collection of dictionaries.
        Individual dictionaries must be serializable. """
    hashes = set(); unique = []
    for object in objects:
        hash = str(object)
        if hash not in hashes:
            hashes.add(hash)
            unique.append(object)
    return unique