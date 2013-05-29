# run-and-report.py
## *Run a command and report to [Riemann](http://riemann.io).*


### Usage
````
Usage: run-and-report.py [options] -- command to run

Options:
  -h, --help            show this help message and exit
  --riemann-host=RIEMANN_HOST
                        The address of Riemann
  --riemann-port=RIEMANN_PORT
                        The port Riemann is running on
  --tags=TAGS           Optional tags for the event
  --ttl=TTL             An optional TTL for the event
  --states=STATES       Describes a mapping of return codes and event states.
                        e.g. ok:0,1|warn:2,3. Return codes without an explicit
                        mapping are assumed error. default=ok:0
  --service=SERVICE     An optional service to the event. Defaults to the
                        basename of the command that's run
  --debug               Output the event before it's sent to Riemann.
````
    
`run-and-report.py` will run the command string and report that the event occurred.
The time it took to run the command will be the metric of th event.
The states argument defines the state of the event based on the return code of the command.
    

### Examples
````
samn@salmon:~ $ run-and-report.py --states "beauty:2,3|ok:0,1" --debug -- ls /dogs
ls: cannot access /dogs: No such file or directory
{'description': '', 'service': 'ls', 'tags': [], 'metric': 0.003847837448120117, 'state': 'beauty', 'host': 'salmon', 'attributes': {'command': 'ls /dogs', 'return_code': 2}}
````    

````
samn@salmon:~ $ run-and-report.py --debug --service 'dogs are cool' --tags dogs,dogges -- 'echo 1 && ls /dogs || echo 2'
ls: cannot access /dogs: No such file or directory
{'description': '1\n2\n', 'service': 'dogs are cool', 'tags': ['dogs', 'dogges'], 'metric': 0.004781007766723633, 'state': 'ok', 'host': 'salmon', 'attributes': {'command': 'echo 1 && ls /dogs || echo 2', 'return_code': 0}}
````
    
### Requirements

* `bernhard` - Python Riemann client
    * requires python-protobuf

### Is it any good?
sure 
