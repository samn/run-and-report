#! /usr/bin/env python
import os.path
import socket
import subprocess
import sys
import time
from optparse import OptionParser

import bernhard

DEFAULT_TAGS = ['run-and-report']

def separate_from_commas(comma_str):
    """
    Takes a string of comma separated elements
    and returns an array of those elements as Strings.
    """
    if comma_str:
        return comma_str.split(",")
    else:
        return []

def kv_array_to_dict(kv_pairs):
    """
    Takes an array of key=value formatted Strings
    and returns a dict
    """

    pairs = {}

    if kv_pairs:
        for kv_string in kv_pairs:
            kv = kv_string.split("=")
            if len(kv) == 2:
                pairs[kv[0]] = kv[1]

    return pairs

def parse_states(states_str):
    """
    Parses a string of state information for interpreting return codes.
    E.g. "ok:0,1|warn:2,3" => {0: "ok", 1: "ok", 2: "warn", 3: "warn"}
    """
    states = {}
    for state_info in states_str.split("|"):
        name, codes = state_info.split(":")
        for code in separate_from_commas(codes):
            states[int(code)] = name
    return states

def run_state(proc, state_table):
    """
    Returns the name of the state that matches the return code of proc.
    Assumes proc has already executed. See parse_states.
    """
    return state_table.get(proc.returncode, "error")

def run_command(command_str):
    proc = subprocess.Popen(command_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    proc.wait()
    return proc

def command_name(command_array):
    command = command_array[0]
    return os.path.basename(command)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--riemann-host", default="localhost", help="The address of Riemann")
    parser.add_option("--riemann-port", default=5555, help="The port Riemann is running on")
    parser.add_option("--tags", default=None, help="Optional tags for the event")
    parser.add_option("--ttl", default=None, help="An optional TTL for the event (in seconds)")
    parser.add_option("--states", default="ok:0", help="Describes a mapping of return codes and event states.  e.g. ok:0,1|warn:2,3. Return codes without an explicit mapping are assumed error. default=ok:0")
    parser.add_option("--service", default=None, help="An optional service to the event. Defaults to the basename of the command that's run")
    parser.add_option("--debug", default=False, action='store_true', help="Output the event before it's sent to Riemann.")
    parser.add_option("--metric-from-stdout", default=False, action='store_true', help="Use stdout as the metric rather than the elapsed command walltime.")
    parser.add_option("--state-from-stdout", default=False, action='store_true', help="Use stdout as the state rather than the elapsed command walltime.")
    parser.add_option("--tcp", default=False, action='store_true', help="Use TCP transport instead of UDP.")
    parser.add_option("--host", default=None, help="Specify hostname.")
    parser.add_option("--omit-metric", default=False, action='store_true', help="Do not send the metric.")
    parser.add_option("--attributes", default=None, help="Comma separated list of key=value attribute pairs. e.g. foo=bar,biz=baz")

    options, command = parser.parse_args()
    if not command:
        print "Fatal: no command given"
        parser.print_help()
        exit(-1)

    command_str = ' '.join(command)
    start = time.time()
    proc = run_command(command_str)
    end = time.time()
    duration = end - start

    state_table = parse_states(options.states)
    service = options.service
    if not service:
        service = command_name(command)

    stdout = proc.stdout.read()
    stderr = proc.stderr.read()
    description = """
    STDOUT >>>
    %s
    <<<
    STDERR >>>
    %s
    <<<
    """ % (stdout, stderr)

    if options.tcp:
        transport = bernhard.TCPTransport
    else:
        transport = bernhard.UDPTransport

    riemann = bernhard.Client(host=options.riemann_host, port=options.riemann_port, transport=transport)

    riemann_event = {}
    riemann_event["service"] = service
    riemann_event["description"] = description

    if options.state_from_stdout:
        riemann_event["state"] = stdout.strip()
    else:
        riemann_event["state"] = run_state(proc, state_table)

    if options.ttl:
        riemann_event["ttl"] = int(options.ttl)

    if options.host:
        riemann_event["host"] = options.host
    else:
        riemann_event["host"] = socket.gethostname()

    if not options.omit_metric:
        if options.metric_from_stdout:
            riemann_event["metric"] = float(stdout)
        else:
            riemann_event["metric"] = duration

    riemann_event["tags"] = DEFAULT_TAGS + separate_from_commas(options.tags)

    attribute_pairs = separate_from_commas(options.attributes)
    riemann_event["attributes"] = kv_array_to_dict(attribute_pairs)
    riemann_event["attributes"]["return_code"] = proc.returncode
    riemann_event["attributes"]["command"] = command_str

    if options.debug:
        print riemann_event

    riemann.send(riemann_event)
    exit(proc.returncode)
