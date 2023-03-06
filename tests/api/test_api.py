import json
from datetime import datetime

import requests

from audio.console import console


def test_api():
    response = requests.get("http://localhost:3000/api/tests")
    data: dict = json.loads(response.content)

    console.log(data)

    date = datetime.strptime(data[0]["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
    console.log(date)

    response = requests.get("http://localhost:3000/api/tests/15")
    data: dict = json.loads(response.content)

    console.log(data)

    date = datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
    console.log(date)

    response = requests.post(
        "http://localhost:3000/api/tests",
        json={
            "name": "Test da Python",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "comment": "Commento da Python",
        },
    )

    console.log(response.content)
