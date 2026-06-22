import datetime
import requests

from prompt_builder import build_prompt


API_URL = "http://localhost:8001/search_hybrid"


def search(query):
    response = requests.get(
        API_URL,
        params={"q": query},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    start = datetime.datetime.now()
    print(f"Start time: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    query = "DataFrame duplicated loses index"

    results = search(query)

    prompt = build_prompt(query, results)

    print(prompt)
    end = datetime.datetime.now()
    print(f"End time: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elapsed: {end - start}")