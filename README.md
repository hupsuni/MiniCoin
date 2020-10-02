MiniCoin - A scaled down blockchain implementation in python.
==============================================================

Deployment:
------------

**Start the bootstrap server.**

*This is required as without the bootstrap new peers will be unable to discover existing peers.*
*This bootstrap server will listen for new connections on port 5000.*
> Bootstrap server:
```console
python3 minicoin.py --type bootstrap
```

**Start some nodes the easy way (recommended).**

*With the bootstrap server running you may now start as many nodes as you like.*
*For ease I recommend starting each node with the optional user interface in a new window.*
*You must specify a unique port number when starting a node of any type by changing the value*
*after the “--port” option.*
> Node with user interface:

```console
python3 minicoin.py --type node-ui --port 5001
```

**Start some nodes the “hard” way (no user interface).**


*Not really that hard.*
*With the bootstrap server running you may start as many new nodes as you like but each node*
*started without a user interface is quite verbose and will print updates to the terminal for many*
*events.*
*As such it is advised that each node is run in a unique terminal or window.*
*You may start a node with no UI as either a simple node or a miner.*
*You must specify a unique port number when starting a node of any type by changing the value*
*after the “--port” option.*


> Simple node:
```console
python3 minicoin.py --type node --port 5002
```
> Miner node:
```console
python3 minicoin.py --type node --port 5003 --mine
```
*A miner node will mine until a user presses enter. It will then stop its mining thread and revert to*
*being a simple node.*
*For convenience, you may also start a simple node that will periodically print its own ledger out*
*in human readable format and then request each of its peers do the same.*
> Periodic printing node:
```console
python3 minicoin.py --type node --port 5004 --print
```
> **Note** *A Mining node cannot operate as a printing node and vice versa.*
