import os
import ssl
import json
import urllib.request

from uuid import uuid4
from datetime import datetime

import flask
import isodate
import amadeus

import utils

flight_searches = {}
locations       = {}

DEBUG_MODE      = os.environ.get("FLASK_ENV", "development") == "development"

def ssl_disabled_urlopen(endpoint):
    context = ssl._create_unverified_context()
    return urllib.request.urlopen(endpoint, context=context)

app = flask.Flask(__name__)
app.secret_key = uuid4().bytes
client = amadeus.Client(http = ssl_disabled_urlopen)

@app.template_filter()
def parse_duration(deltastr):
    return isodate.parse_duration(deltastr)
@app.template_filter()
def parse_datetime(datetimestr):
    return isodate.parse_datetime(datetimestr)
@app.template_filter()
def format_duration(delta, fmtstr):
    return f"{utils.Duration(int(delta.total_seconds())):{fmtstr}}"
@app.template_filter()
def strptime(timestampstr, formatstr):
    return datetime.strptime(timestampstr, formatstr)
@app.template_filter()
def strftime(timestamp, formatstr):
    return timestamp.strftime(formatstr)

@app.route("/")
def index():
    return flask.render_template(
        "base.html.jinja",
        title = "Book Flights like never before",
        today = datetime.now().strftime("%Y-%m-%d")
    )

@app.route("/flights/")
@app.route("/flights/<sort_by>")
def flights(sort_by = "price-wise-asc"):
    if "from" in flask.request.args:
        params = {
            "originLocationCode"     : flask.request.args["from"],
            "destinationLocationCode": flask.request.args["to"],
            "departureDate"          : flask.request.args["depart_on"],
            "adults"                 : flask.request.args.get("adults", 1),
            "children"               : flask.request.args.get("children", 0),
            "infants"                : flask.request.args.get("infants", 0),
            "travelClass"            : flask.request.args.get("class", "ECONOMY"),
            "currencyCode"           : "INR",
            # "includedAirlineCodes"   : "AI"
        }
        if "return_on" in flask.request.args:
            params |= { "returnDate": flask.request.args["return_on"] }

        flask.session["params"] = params | {
            "originLocation"     : flask.request.args["from_location"],
            "destinationLocation": flask.request.args["to_location"],
        }
        flask.session["flights_search_token"] = str(uuid4())

        flight_offers = client.shopping.flight_offers_search.get(**params).result
        for airportCode, location in flight_offers["dictionaries"]["locations"].items():
            if airportCode not in locations:
                try:
                    airport = client.reference_data.location(f"A{airportCode}").get().data
                    flight_offers["dictionaries"]["locations"][airportCode]["airportName"] = airport["name"]
                except amadeus.ResponseError:
                    pass
                try:
                    city = client.reference_data.location(f"C{location['cityCode']}").get().data
                    flight_offers["dictionaries"]["locations"][airportCode] |= city["address"]
                except amadeus.ResponseError:
                    pass
                locations[airportCode] = flight_offers["dictionaries"]["locations"][airportCode]
        flight_searches[flask.session["flights_search_token"]] = flight_offers

        # if DEBUG_MODE:
        #     with open(os.path.join("usr", flask.session["flights_search_token"]+".json"), "w+", encoding="utf-8") as file:
        #         json.dump(flight_searches[flask.session["flights_search_token"]], file, indent=4, ensure_ascii=False)

        return flask.redirect(flask.request.path)
    # elif "flights_search_token" in flask.session:
    origin      = flask.session['params']['originLocationCode']
    destination = flask.session['params']['destinationLocationCode']
    sort_key    = utils.OFFER_SORT_KEYS[sort_by.replace("-asc", "").replace("-desc", "")]
    return flask.render_template(
        "flights.html.jinja",
        params = flask.session["params"],
        flights = sorted(
            flight_searches[flask.session["flights_search_token"]]["data"],
            key = sort_key, reverse="desc" in sort_by
        ),
        locations = locations, sort_keys = utils.OFFER_SORT_KEY_NAMES,
        carriers = flight_searches[flask.session["flights_search_token"]]["dictionaries"]["carriers"],
        aircrafts = flight_searches[flask.session["flights_search_token"]]["dictionaries"]["aircraft"],
        title = f"Cheapest flights from {origin} to {destination}",
        today = datetime.now().strftime("%Y-%m-%d")
    )
    # else:
    #     return flask.redirect("/")

@app.route("/airlinecodes/")
def airlinecodes():
    data = client.reference_data.airlines.get(
        airlineCodes = ','.join(flask.request.args.getlist("airlines"))
    ).data
    for airline in data:
        airline["businessName"] = airline["businessName"].title()
        airline["commonName"  ] = airline["commonName"  ].title()
    return flask.jsonify(data)

@app.route("/iatacodes/")
def iatacodes():
    # return jsonify(utils.get_airport_codes(request.args["query"]))
    data = client.reference_data.locations.get(**{
        "keyword": flask.request.args["query"],
        "subType": amadeus.Location.AIRPORT,
        "view": "LIGHT", "page[limit]": 5
    }).data
    for location in data:
        location["name"] = location["name"].title()
        location["address"]["cityName"] = location["address"]["cityName"].title()
        location["address"]["countryName"] = location["address"]["countryName"].title()
        del location["self"]
    return flask.jsonify(data)