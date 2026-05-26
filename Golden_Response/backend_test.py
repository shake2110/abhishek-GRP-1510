import requests

URL = 'http://127.0.0.1:5000/analyze'

sample_reviews = [
    "The camera quality is excellent, but the battery drains quickly.",
    "Battery life is amazing and the display is crisp.",
    "Not happy with the build quality, but the looks are great."
]

for r in sample_reviews:
    resp = requests.post(URL, json={'review': r})
    print('Review:', r)
    print('Status:', resp.status_code)
    try:
        print('Response:', resp.json())
    except Exception as e:
        print('Non-JSON response:', resp.text)
    print('---')
