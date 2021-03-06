# flight-recorder

Daemon which tracks system crashes and downtime duration

flight-recorder is a more portable replacement for [downtimed](https://github.com/snabb/downtimed) which also works on devices without real-time clock (like Raspberry Pi). These devices rely on network time server to set system time once network connection becomes available. For this reason precise time is not available at system startup and it doesn't allow to estimate uptime gaps right away.

flight-recorder doesn't rely on any system-specific calls to get wall-clock time of system startup. Instead, each instance of flight-recorder generates unique ID of it's run (flight) and tracks it's duration with monotonic clock. Daemon keeps duration record updated in database (SQLite) and at the same time updates perceived wall-clock timestamp for it's flight ID. Once network will become available and system time is syncronized with NTP, flight record will eventually become grounded to actual wall-clock time with proper uptime boundaries. "Flights" may overlap if multiple instances of daemon are running at the same time.

---

:heart: :heart: :heart:

You can say thanks to the author by donations to these wallets:

- ETH: `0xB71250010e8beC90C5f9ddF408251eBA9dD7320e`
- BTC:
  - Legacy: `1N89PRvG1CSsUk9sxKwBwudN6TjTPQ1N8a`
  - Segwit: `bc1qc0hcyxc000qf0ketv4r44ld7dlgmmu73rtlntw`

---

## Features

* Cross-platform (Linux/MacOS/Windows/\*BSD/whatever that can run Python)
* Works well on devices without real-time clock (like Raspberry Pi and other mini-computers)
* Common storage format (SQLite)
* Doesn't hurts to device flash by rewriting same file blocks: SQLite storage backend operates in WAL mode
* Handles overlapped uptime tracks from multiple instances
* Can be operated by unprivileged user (both daemon and report utility)

## Usage

Run `flight-recorder` in background on server startup and use `flight-reports` to print reports.

Make sure database path used by `flight-recorder` matches path used by `flight-reports`.

## Example output

```
$ flight-reports -d /var/lib/flight-recorder/flight.db
DOWNTIME #1: -INF => 2020-06-17 03:05:05 (INF)

UPTIME #1: 2020-06-17 03:05:05 => 2020-06-17 03:15:25 (0:10:20.586976)
	FLIGHT #1: 2020-06-17 03:05:05 => 2020-06-17 03:15:25 (0:10:20.586976)
DOWNTIME #2: 2020-06-17 03:15:25 => 2020-06-17 03:16:31 (0:01:05.631327)

UPTIME #2: 2020-06-17 03:16:31 => 2020-06-17 04:55:17 (1:38:46.525753)
	FLIGHT #2: 2020-06-17 03:16:31 => 2020-06-17 04:55:17 (1:38:46.525753)
```


## Requirements

Python 3.5+

## Installation

Place scripts somewhere and just run them as you like.

Example (run as root):

```sh
git clone https://github.com/Snawoot/flight-recorder.git && \
cd flight-recorder && \
install flight-recorder flight-reports /usr/local/bin && \
useradd -r -s /usr/sbin/nologin -m -d /var/lib/flight-recorder flight-recorder && \
install -m 0644 flight-recorder.service /etc/systemd/system && \
systemctl daemon-reload && \
systemctl enable flight-recorder.sevice && \
systemctl start flight-recorder.service
```

Done, now you may see reports:

```
flight-reports -d /var/lib/flight-recorder/flight.db
```


## Synopsis

```
$ ./flight-recorder -h
usage: flight-recorder [-h] [-i INTERVAL] [-v {debug,info,warn,error,fatal}] [-l LOG] [-d DATABASE]

Tracks system crashes and downtime duration

optional arguments:
  -h, --help            show this help message and exit

flight options:
  -i INTERVAL, --interval INTERVAL
                        interval between flight record updates (default: 10.0)

output options:
  -v {debug,info,warn,error,fatal}, --verbosity {debug,info,warn,error,fatal}
                        logging verbosity (default: info)
  -l LOG, --log LOG     output messages to log file instead of stderr (default: None)
  -d DATABASE, --database DATABASE
                        database path (default: /home/user/.flight-recorder/flight-recorder.db)
```

```
$ ./flight-reports -h
usage: flight-reports [-h] [-d DATABASE]

Reports system crashes and downtime duration

optional arguments:
  -h, --help            show this help message and exit
  -d DATABASE, --database DATABASE
                        database path (default: /home/user/.flight-recorder/flight-recorder.db)
```
