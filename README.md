Instructions:

1. Replace the default values in `settings.py` as desired
2. You can get the free API Key from https://polygon.io/.

Running locally:

1. To run type `POLYGON_API_KEY="<api_key>" python3 main.py`

Running on Github CI:

1. Fork this repo
2. Go to `Settings` -> `Secrets and Variables` -> `Actions`
3. Added a Repository Secret called `POLYGON_API_KEY` and should be your Polygon API Key
4. Now whenever you make a Pull request wait for the CI to finish (the longest time will be in the Polygon call with free licenses. It is limited to 5 calls a minute)
5. Once your CI is done go to `Actions` -> Click on the latest run -> You will see the artifacts called `run-results`. Download it

TODO:

- [ ] Implement long and short options correctly. Currently they are implemented same as stocks
- [ ] Investigate other API's that provide realtime data and are stable (For example: YFinance is good but it delists options that have expired)
