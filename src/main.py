#!/usr/bin/env python3

import importlib
import json
import asyncio
import os
import argparse
import traceback
import util.print

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--dryrun",
    action="store_true",
    help="Output fetched IPs without updating DNS",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Output extra info while running",
)


def load_config(path):
    try:
        configPath = os.getcwd() + path
        with open(configPath, "r+") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        raise ValueError("Config file not present at: " + configPath)


async def main():
    args = parser.parse_args()
    config = load_config("/config.json")
    ipRecord = dict()
    ipRecordSink = dict()
    for source in config["sources"]:
        try:
            conf = config["sources"][source]
            module = importlib.import_module(
                "sources." + conf["type"])
            ipRecord[source] = await module.fetch_ip(conf)
        except Exception:
            print("Error while fetching IPs for " + source + ":")
            print(traceback.format_exc())
    if args.dryrun or args.verbose:
        print("Fetched IPs")
        print(util.print.format_iprecords(ipRecord))
    for sink in config["sinks"]:
        try:
            conf = config["sinks"][sink]
            module = importlib.import_module(
                "sinks." + conf["type"])
            ipRecordSink[sink] = await module.update_ips(conf, ipRecord, dryrun=args.dryrun, verbose=args.verbose)
        except Exception:
            print("Error while updating IPs for " + sink + ":")
            print(traceback.format_exc())
    # TODO Optional cache to retain ipRecordSink for next run to reduce API calls


if __name__ == "__main__":
    asyncio.run(main())
