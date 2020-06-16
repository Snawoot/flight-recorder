#!/usr/bin/env python3

import argparse
import logging
import sqlite3
import time
import enum
import os
import os.path
import signal

DB_INIT = [
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "CREATE TABLE IF NOT EXISTS flight (\n"
    "id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "duration REAL NOT NULL CONSTRAINT positive_duration CHECK (duration >= 0),\n"
    "last_ts REAL NOT NULL)",
    "CREATE INDEX IF NOT EXISTS idx_flight_last_ts\n"
    "ON flight (last_ts)\n",
    "CREATE INDEX IF NOT EXISTS idx_flight_begin\n"
    "ON flight (last_ts - duration)\n",
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
        description="Tracks system crashes and downtime duration",
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

class Recorder:
    def __init__(self, conn, interval=10.):
        self._conn = conn
        self._interval = interval
        self._logger = logging.getLogger("RECORDER")
        self._flight_id = None
        self._started_mono = None
        self._cur = None

    def _create_flight(self):
        ts = time.time()
        with self._conn:
            self._cur.execute("INSERT INTO flight (duration, last_ts) VALUES (?,?)",
                              (time.monotonic() - self._started_mono, ts))
        self._flight_id = self._cur.lastrowid
        self._logger.info("Opened flight record #%d: ts=%.3f", self._flight_id, ts)

    def _update_flight(self):
        ts = time.time()
        new_duration = time.monotonic() - self._started_mono
        with self._conn:
            self._cur.execute("UPDATE flight SET duration = ?, last_ts = ? WHERE id = ?",
                              (new_duration, ts, self._flight_id))
        self._logger.info("Updated flight record #%d: duration=%.3f ts=%.3f",
                          self._flight_id, new_duration, ts)

    def run(self):
        self._started_mono = time.monotonic()
        self._cur = self._conn.cursor()
    
        try:
            self._create_flight()
        except Exception as exc:
            self._logger.critical("Unable to create flight record: %s", str(exc))
            self._cur.close()
            return
    
        try:
            while True:
                time.sleep(self._interval)
                try:
                    self._update_flight()
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    self._logger.error("DB update failed: %s", str(exc))
        except KeyboardInterrupt:
            self._update_flight()
        finally:
            self._cur.close()
            self._logger.info("Flight record #%d closed.", self._flight_id)

def sig_handler(signum, frame):
    raise KeyboardInterrupt

def main():
    signal.signal(signal.SIGTERM, sig_handler)
    args = parse_args()
    logger = setup_logger("MAIN", args.verbosity, args.log)
    setup_logger("RECORDER", args.verbosity, args.log)

    try:
        conn = ensure_db(args.database)
    except Exception as exc:
        logger.critical("DB connection failed: %s", str(exc))
        return

    logger.info("Starting flight recorder...")
    recorder = Recorder(conn, args.interval)
    try:
        recorder.run()
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()
        logger.info("Flight recorder shut down.")

if __name__ == '__main__':
    main()
