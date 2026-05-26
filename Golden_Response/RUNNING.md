Backend run & test

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate  # on Windows
pip install -r requirements.txt
```

2. (Optional) Set `MONGO_URI` environment variable if you are not using the default local MongoDB.

3. Run the backend:

```bash
python app.py
```

4. In another terminal run the quick tester to POST sample reviews:

```bash
python backend_test.py
```

If you see JSON responses with `positive`, `negative`, or `neutral` sentiments, the backend submit flow is working.
