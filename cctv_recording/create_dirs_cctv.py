#!/usr/bin/python3

import pathlib
import logging
import datetime
import json
import os
from utils.config import genconf

config = genconf()


def create_directories_for_next_day():
    year = ""
    month = ""
    day = ""

    # Check if tomarrow is new year - then create new year directory
    year_diff = (
        datetime.date.today() + datetime.timedelta(days=1)
    ).year - datetime.datetime.now().year
    if year_diff > 0:
        year = str((datetime.date.today() + datetime.timedelta(days=1)).year)
    else:
        year = str(datetime.datetime.now().year)

    # Check if tomarrow is new month - then create new year directory
    month_diff = (
        datetime.date.today() + datetime.timedelta(days=1)
    ).month - datetime.datetime.now().month
    if month_diff > 0:
        month = str((datetime.date.today() + datetime.timedelta(days=1)).month)
    else:
        month = str(datetime.datetime.now().month)

    if int(month) < 10:
        month = f"0{month}"

    # Create next day directory
    day += str((datetime.date.today() + datetime.timedelta(days=1)).day)
    if int(day) < 10:
        day = f"0{day}"

    for camera in config.cameras:
        dir_name = pathlib.Path(config.cameras_dir, camera.name, year, month, day)
        dir_name.mkdir(parents=True, exist_ok=True)
        logging.debug(f'Created directory for day "{dir_name}"')


create_directories_for_next_day()
