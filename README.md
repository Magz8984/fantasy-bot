# How to run

1. Activate virtual environment

```
source venv/bin/activate
```

2. Install requirements in VENV

```
    pip install -r requirements.txt
```

3. Run

```
firebase emulators:start --only functions
```

4. Deploy

```
firebase deploy --only functions
```
