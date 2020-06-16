# flight-recorder
Daemon which tracks system crashes and downtime duration

## Usage

Run `flight-recorder` in background on server startup and use `flight-reports` to print reports.

Make sure database path used by `flight-recorder` matches path used by `flight-reports`.

## Requirements

Python 3.5+

## Installation

Place scripts somewhere and just run them as you like.

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
