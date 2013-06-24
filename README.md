selenium-grid-node-manager
==========================

Short description
-----------------
XML-RPC based tool to allow remote management of selenium grid machines.

----
#### Note: *it's initial repo*
 - code is still work in progress


Installation:
------

Just clone repo to any folder and start manager as service or directly:
- run manager as a Windows service or Unix daemon
  ```bash
  $ python node-manager.py -h
  ```

- execute manager directly
  ```bash
  $ python src/nodemanager.py -h
  ```

Usage:
------
Example usages are:
#####Python:
```python
import xmlrpclib

s = xmlrpclib.ServerProxy('http://localhost:5005')
s.system.listMethods()
```

Dependencies:
-------------
  - running as windows service requires _python win extensions_ [__pywin32__ (win32all)](http://sourceforge.net/projects/pywin32/files/)