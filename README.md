Instructions:

1. Replace the default values in `portfolio.yaml` as desired
2. Check the starting all caps values in the file you want to run and modify as needed
3. You can get the free API Key from https://polygon.io/.

Running locally:

1. To run type `API_KEY="<api_key>" python3 portfolio.py`

Running on Github CI:

1. Fork this repo
2. Go to `Settings` -> `Secrets and Variables` -> `Actions`
3. Added a Repository Secret called `POLYGON_API_KEY` and should be your Polygon API Key
4. Now whenever you make a Pull request wait for the CI to finish (the longest time will be in the Polygon call with free licenses. It is limited to 5 calls a minute)
5. Once your CI is done go to `Actions` -> Click on the latest run -> You will see the artifacts called `run-results`. Download it

