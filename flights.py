#!/usr/bin/env python3

import sys
import argparse
import logging
import sqlite3
import time
import enum
import os
import os.path

QUERY = """
SELECT id,
       TRUE,
       last_ts - duration AS ts
FROM flight
UNION ALL
SELECT id,
       FALSE,
       last_ts
FROM flight
ORDER BY ts
"""

MINUS_INF = float("-inf")
PLUS_INF = float("+inf")

class Event(enum.Enum):
    DOWNTIME = 0
    FLIGHT = 1

def parse_args():
    parser = argparse.ArgumentParser(
        description="Reports system crashes and downtime duration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    def_db_path = os.path.join(os.path.expanduser("~"),
                               ".flight-recorder", "flight-recorder.db")
    parser.add_argument("-d", "--database",
                        help="database path",
                        default=def_db_path)
    return parser.parse_args()

def gen_ranges(conn):
    cur = conn.cursor()
    last_uptime = MINUS_INF
    open_ranges = dict()
    downtime_id = 1
    try:
        cur.execute(QUERY)
        for row in cur:
            flight_id, is_open, ts = row
            if is_open:
                if not open_ranges:
                    # Gap detected - yield DOWNTIME
                    yield Event.DOWNTIME, (downtime_id, last_uptime, ts)
                    downtime_id += 1
                open_ranges[flight_id] = ts
            else:
                yield Event.FLIGHT, (flight_id, open_ranges[flight_id], ts)
                open_ranges.pop(flight_id)
                last_uptime = ts
    finally:
        cur.close()

def report(conn):
    for x in gen_ranges(conn):
        print(x)

def main():
    args = parse_args()

    try:
        conn = sqlite3.connect(args.database)
    except Exception as exc:
        print("DB connection failed: %s" % str(exc), file=sys.stderr)
        raise SystemExit(3)

    try:
        report(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
