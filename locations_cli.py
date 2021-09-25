import ssl
import urllib.request

import amadeus

def ssl_disabled_urlopen(endpoint):
    context = ssl._create_unverified_context()
    return urllib.request.urlopen(endpoint, context=context)

client = amadeus.Client(
    client_id = "4gk9l2gDGsXj0Hmx3bHhFfOrNfLqhejW",
    client_secret = "CBiZteVVhJP5T1fN",
    http = ssl_disabled_urlopen
)

if __name__ == "__main__":
    keyword = input("Enter a search term: ")
    try:
        result = client.reference_data.locations.get(
            keyword = keyword, subType = amadeus.Location.ANY, view = "LIGHT"
        )
        data = result.body
        print(data)
        for i, location in enumerate(result.data, start=1):
            print(f"#{i}", location["subType"], ":", location["name"])
    except amadeus.ResponseError as e:
        print(e.error_description(e.response))