# Something something walmart supply chain optimization
Contains dummy agent setup using simulated data instead of relying on routing APIs, need to fix this- though the methods for calculating distance between two points should be working. Probably missing a bunch of other things as well, but welp (°ー°〃)


Good luck with the data and the external routing api integration! (✿◡‿◡)

Please bother me if any of this becomes a PITA



## Run
```
uv run main.py  # for demo 
```

## Env vars
```
SERPER_API_KEY=1e5feb0f7ce4199d7c275f841a618991b66a810f
GEMINI_API_KEY=it's free :D
```


`crew.py` contains the main logic and the three agents: `SupplyChainManager`, `LogisticsCoordinator`, and `DemandAnalyst`. (lines 278-324)

Ignore the API, it was a mistake(born during vibecoding fit) and should be killed with abortion pills(post vibecoding, the human realizes it is better to cut the problem at its roots instead of giving himself false hopes of a reduced workload). 