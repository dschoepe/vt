#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vt - Simple västtrafik client
# Copyright (C) 2014 Daniel Schoepe
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import requests
import json
import os
import sys
import re
import xdg.BaseDirectory
import dateutil.parser
import colorama
from importlib import import_module
import argparse
from colorama import Fore, Back, Style
from datetime import time, timedelta
from tabulate import tabulate


def prepare_stop(stop):
    """Apply pretty-printers and sanitisation to stop."""
    sanitize_stop(stop)
    stop["name"] = pp_name(stop["name"])
    try:
        # calculate difference between real time data and scheduled:
        time = dateutil.parser.parse(stop['date'] + " " + stop['time'])
        stop['datetime'] = time
        rt_time = dateutil.parser.parse(stop['rtDate'] + " " + stop['rtTime'])
        stop['rt_datetime'] = rt_time
        delta = rt_time - time
        stop["timedelta"] = int(delta.total_seconds() / 60)
    except Exception as e:
        debug(e)
        debug("Failed to parse time")
        stop["timedelta"] = None


def colorize_line(line):
    """Colorize the given bus/tram line.

    Due to the limited amount of colors available in many terminals,
    this doesn't quite match Västtrafik's color scheme."""
    colors = {'1': Back.WHITE + Fore.BLUE,
              '2': Back.YELLOW + Style.BRIGHT + Fore.BLUE,
              '3': Back.BLUE + Style.DIM + Fore.WHITE,
              '4': Back.GREEN + Style.DIM + Fore.WHITE,
              '5': Back.RED + Style.BRIGHT + Fore.WHITE,
              '6': Back.RED + Style.DIM + Fore.BLACK,
              '7': Back.RED + Style.DIM + Fore.WHITE,
              '8': Back.MAGENTA + Style.DIM + Fore.WHITE,
              '9': Back.CYAN + Fore.WHITE,
              '10': Back.YELLOW + Style.BRIGHT + Fore.BLACK,
              '11': Back.BLACK + Style.BRIGHT + Fore.WHITE,
              '13': Back.WHITE + Style.DIM + Fore.BLUE}
    for l in range(16, 20):
        colors[str(l)] = Back.BLUE + Fore.GREEN + Style.BRIGHT
    return colors.get(line, Back.BLUE + Style.BRIGHT) + line + Style.RESET_ALL


def pp_leg(leg, orig, dest):
    """Pretty-print one leg of a journey (also used for summaries)."""
    prepare_stop(orig)
    prepare_stop(dest)

    def print_time(s):
        result = ""
        if opts.date is not None:
            result += s['date']+" "
        if s['timedelta'] != 0 and s['timedelta'] is not None:
            if s['timedelta'] > 0:
                col = Fore.RED
            else:
                col = Fore.GREEN
            return result + ("(%s %s%+d%s)" %
                             (s['time'], col, s['timedelta'], Fore.RESET))
        else:
            return result + ("(%s)" % (s['time']))

    def print_stop(s):
        return "{name}[{track}]".format(name=s['name'], track=s['track'])
    totalmins = (dest['datetime'] - orig['datetime']).total_seconds() // 60
    totaltime = "%02d:%02d" % (totalmins // 60, totalmins % 60)
    # If we're not in a summary entry, add line information to result
    if 'sname' in leg:
        bus = colorize_line(leg['sname'])
    else:
        bus = None
    return {'orig_time': print_time(orig),
            'orig_stop': print_stop(orig),
            'separator': ("--[%s]-->" % totaltime) if bus is None
            else ("--[%s, %s]-->" % (bus, totaltime)),
            'dest_time': print_time(dest),
            'dest_stop': print_stop(dest),
            # keep total time around to filter out bogus trips later
            'total_mins': totalmins}


def pp_name(name):
    """Pretty-print the name of a stop."""
    return re.sub(', Göteborg$', '', name)


def pp_trip(trip):
    """Pretty-print one trip."""
    legs = trip['Leg']
    if isinstance(legs, dict):
        orig = legs['Origin']
        dest = legs['Destination']
        return {'summary': pp_leg(legs, orig, dest)}
    else:
        # multi-stage trip:
        result = {'summary': pp_leg({}, legs[0]['Origin'],
                                    legs[len(legs)-1]['Destination'])}
        if not opts.short:
            result['details'] = filter(lambda l: l['total_mins'] != 0,
                                       map(lambda l: pp_leg(l, l['Origin'],
                                                            l['Destination']),
                                           legs))
        return result


def print_trips(src, dest):
    """Display trips between origin and destination."""
    def toRow(s):
        return [s['orig_time'], s['orig_stop'], s['separator'],
                s['dest_time'], s['dest_stop']]
    trips = [pp_trip(x) for x in trips_from_to(src, dest)]
    table = [toRow(t['summary']) for t in trips]
    headers = ["Time", "Stop", "", "Time", "Stop"]
    lines = tabulate(table, headers=headers).splitlines()
    print(lines[0])
    print(lines[1])
    for (l, t) in zip(lines[2:], trips):
        print(l)
        if 'details' in t:
            detailTable = [toRow(l) for l in t['details']]
            head, *mid, tail = tabulate(detailTable).splitlines()
            print("\t* "+head)
            for l2 in mid:
                print("\t| " + l2)
            print("\t* "+tail)


def load_config():
    """Execute the configuration file as python code."""
    configdir = os.path.join(xdg.BaseDirectory.xdg_config_home, "vt")
    configfile = os.path.join(configdir, "config.py")
    if os.path.exists(configfile):
        sys.path.insert(0, configdir)
        try:
            global config
            config = import_module('config')
            if not hasattr(config, 'aliases'):
                config.aliases = {}
            for attr in ["default_origin", "default_destination", "auth_key"]:
                if not hasattr(config, attr):
                    setattr(config, attr, None)
        except Exception as e:
            die("Failed to load config. Make sure %s is valid" % configfile, e)
    else:
        die("Config file doesn't exist")


def perform_query(url, params):
    """Perform a query with given parameters."""
    baseParams = {'authKey': config.auth_key, 'format': 'json'}
    paramsMerged = dict(baseParams, **params)
    r = requests.get(url, params=paramsMerged)
    return r.json()


def trip_query(params):
    tripurl = "http://api.vasttrafik.se/bin/rest.exe/v1/trip"
    return perform_query(tripurl, params)


def locationName(params):
    locationNameUrl = "http://api.vasttrafik.se/bin/rest.exe/v1/location.name"
    return perform_query(locationNameUrl, params)


def name_completions(name):
    """Return a list of completions for given (prefix of a) stop name."""
    r = locationName({'input': name})
    return [loc['name'] for loc in r['LocationList']['StopLocation']]


def id_by_name(name):
    """Get stop id for name of stop."""
    resp = locationName({'input': name})
    try:
        result = resp['LocationList']['StopLocation'][0]['id']
        return result
    except:
        die("No such stop found")


def handle_stop_name(name):
    """Translate stop name aliases to their full names."""
    return config.aliases.get(name, name)


def trips_fromto_raw(src, dest):
    srcId = id_by_name(handle_stop_name(src))
    destId = id_by_name(handle_stop_name(dest))
    params = {'originId': srcId,
              'destId': destId}
    if opts.time is not None:
        try:
            t = dateutil.parser.parse(opts.time)
            params['time'] = t.strftime("%H:%M")
        except Exception as e:
            die("Failed to parse time: " + opts.time)
    if opts.date is not None:
        try:
            d = dateutil.parser.parse(opts.date)
            params['date'] = d.strftime("%Y-%m-%d")
        except:
            print("Failed to parse date: " + opts.date)
    return trip_query(params)


def trips_from_to(src, dest):
    try:
        return trips_fromto_raw(src, dest)['TripList']['Trip']
    except Exception as e:
        die("Failed to look up trip", e)


def sanitize_stop(stop):
    """Add fields to stop records that other functions assume to exist."""
    neededKeys = ["rtTime", "track"]
    for k in neededKeys:
        if k not in stop.keys():
            stop[k] = None


def debug(msg):
    if opts.debug:
        print(msg)


def die(msg, exception=None):
    """Print a message, then exit. Print exception too if one is given."""
    print(msg)
    if exception is not None:
        print(exception)
    parser.print_help()
    sys.exit(1)


def main():
    """Main entry point."""
    colorama.init()
    usage = '''
%(prog)s [options] FROM TO
       %(prog)s [options] TO
       %(prog)s [options]
'''[1:-1]
    global parser
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument("-s", "--short",
                        help="Show only trip summaries.",
                        action="store_true", default=False)
    parser.add_argument("-t", "--time", help="Time of departure.")
    parser.add_argument("-d", "--date", help="Date of departure.")
    parser.add_argument("-r", "--raw", help="Print raw JSON data.",
                        action="store_true", default=False)
    parser.add_argument("-c", "--complete",
                        help="Show possible completions "
                        "for stop name instead of searching for trips (used "
                        "by ZSH completion).", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", dest="debug",
                        help="Print debug output.", action="store_true",
                        default=False)
    parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)
    load_config()
    global opts
    opts = parser.parse_args()
    args = opts.args
    if config.auth_key is None:
        die("No auth_key given. "
            "See http://labs.vasttrafik.se/ for instructions.")
    if opts.complete:
        if len(args) != 1:
            die("Expected (partial) stop name to complete")
        for compl in name_completions(args[0]):
            print(compl)
    else:
        if len(args) == 2:
            origin = args[0]
            dest = args[1]
        elif len(args) == 1 and config.default_origin is not None:
            origin = config.default_origin
            dest = args[0]
        elif len(args) == 0 and\
                config.default_origin is not None and\
                config.default_destination is not None:
            origin = config.default_origin
            dest = config.default_destination
        else:
            die("Invalid number of arguments.")
        if opts.raw:
            print("Search for trip from %s to %s" % (origin, dest))
            print(trips_fromto_raw(origin, dest))
        else:
            print_trips(origin, dest)

if __name__ == "__main__":
    main()
