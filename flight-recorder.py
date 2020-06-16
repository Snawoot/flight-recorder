#!/usr/bin/env python3

import argparse
import logging
import sqlite3
import time
import enum
import os
import os.path

DB_INIT = [
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "CREATE TABLE IF NOT EXISTS flight (\n"
    "id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "interval REAL NOT NULL,\n"
    "updated REAL NOT NULL)",
    "CREATE INDEX IF NOT EXISTS idx_flight_updated\n"
    "ON flight (updated)\n",
]

def setup_logger(name, verbosity, logfile=None):
    logger = logging.getLogger(name)
    logger.setLevel(verbosity)
    if logfile:
        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler()
    handler.setLevel(verbosity)
    handler.setFormatter(logging.Formatter("%(asctime)s "
                                           "%(levelname)-8s "
                                           "%(name)s: %(message)s",
                                           "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    return logger

class LogLevel(enum.IntEnum):
    debug = logging.DEBUG
    info = logging.INFO
    warn = logging.WARN
    error = logging.ERROR
    fatal = logging.FATAL
    crit = logging.CRITICAL

    def __str__(self):
        return self.name

def parse_args():
    def check_loglevel(arg):
        try:
            return LogLevel[arg]
        except (IndexError, KeyError):
            raise argparse.ArgumentTypeError("%s is not valid loglevel" % (repr(arg),))

    def check_positive_int(arg):
        def fail():
            raise argparse.ArgumentTypeError("%s is not valid positive integer" % (repr(arg),))
        try:
            ivalue = int(arg)
        except ValueError:
            fail()
        if ivalue <= 0:
            fail()
        return ivalue

    def check_positive_float(arg):
        def fail():
            raise argparse.ArgumentTypeError("%s is not valid positive float" % (repr(arg),))
        try:
            fvalue = float(arg)
        except ValueError:
            fail()
        if fvalue <= 0:
            fail()
        return fvalue

    parser = argparse.ArgumentParser(
        description="Fetches free proxy list via Hola browser extension API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    flight_group = parser.add_argument_group("flight options")
    flight_group.add_argument("-i", "--interval",
                              default=10.0,
                              type=check_positive_float,
                              help="interval between flight record updates")
    output_group = parser.add_argument_group("output options")
    output_group.add_argument("-v", "--verbosity",
                              help="logging verbosity",
                              type=check_loglevel,
                              choices=LogLevel,
                              default=LogLevel.info)
    output_group.add_argument("-l", "--log",
                              help="output messages to log file instead of stderr")
    def_db_path = os.path.join(os.path.expanduser("~"),
                               ".flight-recorder", "flight-recorder.db")
    output_group.add_argument("-d", "--database",
                              help="database path",
                              default=def_db_path)
    return parser.parse_args()

def ensure_db(db_path):
    os.makedirs(os.path.dirname(db_path), mode=0o755, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for q in DB_INIT:
        cur.execute(q)
    conn.commit()
    cur.close()
    return conn

def recorder(args):
    logger = logging.getLogger("RECORDER")
    try:
        conn = ensure_db(args.database)
    except Exception as exc:
        logger.critical("DB connection failed: %s", str(exc))
        return
    cur = conn.cursor()

    try:
        ts = time.time()
        try:
            cur.execute("INSERT INTO flight (interval, updated) VALUES (?,?)",
                        (args.interval, ts))
        except Exception as exc:
            logger.critical("Unable to create flight record: %s", str(exc))
            return
        flight_id = cur.lastrowid
        logger.info("Opened flight record id=%d, interval=%.3f, ts=%.3f",
                    flight_id, args.interval, ts)
    except KeyboardInterrupt:
        pass
    finally:
        cur.close()
        conn.close()
        logger.info("Flight record closed.")

def main():
    args = parse_args()
    logger = setup_logger("MAIN", args.verbosity, args.log)
    setup_logger("RECORDER", args.verbosity, args.log)
    logger.info("Starting flight recorder...")
    try:
        recorder(args)
    finally:
        logger.info("Flight recorder shut down.")

if __name__ == '__main__':
    main()
