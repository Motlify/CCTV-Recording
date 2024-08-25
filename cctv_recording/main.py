#!/usr/bin/python3

import logging
import subprocess
import pathlib
from sys import stdout
from kafka import KafkaProducer
import os
import datetime
import asyncio
import time
from utils.config import genconf, configure_logging, Camera

configure_logging()
config = genconf()

CAMERAS_DIR = config.cameras_dir


timeout_string = "-timeout"


def create_directory_for_cam(camera: Camera):
    # Create inital dir for today
    year = str(datetime.datetime.now().year)
    month = str(datetime.datetime.now().month)
    if int(month) < 10:
        month = f"0{month}"
    day = str(datetime.datetime.now().day)
    if int(day) < 10:
        day = f"0{day}"
    dir_name = pathlib.Path(CAMERAS_DIR, camera.name, year, month, day)
    dir_name.mkdir(parents=True, exist_ok=True, mode=0o1777)
    logging.debug(f'Created directory for day "{dir_name}"')


def start_camera_snapshoting_images(camera: Camera):
    logging.info(f"[Camera {camera.name}] Starting capture image for camera")
    try:
        if config.still_images == "raw_files":
            image_file_name = camera.name + "-" + "still.jpg"
            image_output_path = pathlib.Path(CAMERAS_DIR, "still_image")
            image_output_path.mkdir(parents=True, exist_ok=True)
            still_image_path = str(pathlib.Path(image_output_path, image_file_name))
            while True:
                time.sleep(config.still_image_interval)
                p = subprocess.run(
                    [
                        "ffmpeg",
                        "-loglevel",
                        "panic",
                        "-rtsp_transport",
                        "tcp",
                        "-i",
                        camera.url,
                        "-frames",
                        "1",
                        "-y",
                        still_image_path,
                    ]
                )
        elif config.still_images == "kafka":
            # Kafka setup
            kafka_bootstrap_servers = config.kafka.api_url
            kafka_topic = config.kafka.images_topic
            # Create Kafka producer
            producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers)
            while True:
                time.sleep(config.still_image_interval)
                p = subprocess.run(
                    [
                        "ffmpeg",
                        "-loglevel",
                        "panic",
                        "-rtsp_transport",
                        "tcp",
                        "-i",
                        camera.url,
                        "-frames",
                        "1",
                        "-f",
                        "image2pipe",
                        "-",
                    ],
                    capture_output=True,
                )
                # Publish the image bytes to a Kafka topic
                producer.send(
                    kafka_topic,
                    headers=[
                        ("camera", bytes(camera.name, encoding="utf8")),
                        (
                            "timestamp",
                            bytes(
                                str(
                                    datetime.datetime.timestamp(datetime.datetime.now())
                                ),
                                encoding="utf8",
                            ),
                        ),
                    ],
                    value=p.stdout,
                ).get(timeout=20)
    except Exception as e:
        logging.error(
            f"[Camera {camera.name}] Could not capture still-image: {e}.\n Retrying in {config.still_image_interval} seconds."
        )
        time.sleep(config.still_image_interval)
        start_camera_snapshoting_images(camera)


def start_recording_camera(camera: Camera):
    """Start ffmpeg process to record camera feed in specified (UNIX) directory"""
    if len(camera.url) > 0 and len(camera.name) > 0:
        create_directory_for_cam(camera)
        logging.info(f"[Camera {camera.name}] Starting recording camera")

        video_file_name = camera.name + "-" + "%Y-%m-%d_at_%H-%M-%S.mkv"
        video_output_path = pathlib.Path(CAMERAS_DIR, camera.name)
        video_output_path = str(video_output_path) + "/%Y/%m/%d/" + video_file_name

        p = subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "panic",
                "-rtsp_transport",
                "tcp",
                timeout_string,
                "30000000",
                "-i",
                camera.url,
                "-c",
                "copy",
                "-map",
                "0",
                "-reset_timestamps",
                "1",
                "-strftime",
                "1",
                "-avoid_negative_ts",
                "1",
                "-f",
                "segment",
                "-segment_time",
                "900",
                "-segment_format",
                "mkv",
                video_output_path,
            ]
        )
        logging.error(f"[Camera {camera.name}] Camera recording died for more than 30s")
        start_recording_camera(camera)


def start_camera_snaphosting_audio(camera: Camera):
    """Start ffmpeg to record audio from camera to temporary file (UNIX)"""
    if len(camera.url) > 0 and len(camera.name) > 0 and camera.audio:
        try:
            logging.info(f"[Camera {camera.name}] Starting recording audio")
            # Get 1 minute of audio from camera
            # Create Kafka producer
            kafka_bootstrap_servers = config.kafka.api_url
            kafka_topic = config.kafka.audio_topic
            producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                max_request_size=20971520,
                buffer_memory=20971520 * 3,
            )
            while True:
                # Run the FFmpeg command to record audio from the RTSP feed
                command = f"ffmpeg -i {camera.url} -t {config.audio_duration} -f wav -acodec pcm_s16le -ar 16000 -ac 2 -"
                process = subprocess.Popen(
                    command.split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
                )
                # Read the output from the FFmpeg process
                output, _ = process.communicate()

                # Store the audio data in a variable
                audio_data = output

                # Send to MQ recorded audio binary data
                producer.send(
                    kafka_topic,
                    headers=[
                        ("camera", bytes(camera.name, encoding="utf8")),
                        (
                            "timestamp",
                            bytes(
                                str(
                                    datetime.datetime.timestamp(datetime.datetime.now())
                                ),
                                encoding="utf8",
                            ),
                        ),
                    ],
                    value=audio_data,
                ).get(timeout=20)
        except Exception as e:
            logging.error(
                f"[Camera {camera.name}] Could not record audio: {e}.\n Retrying to record audio"
            )
            start_camera_snaphosting_audio(camera)


async def main():
    logging.info("Starting scheduling")
    funcs = [start_recording_camera]
    if config.kafka:
        funcs.extend([start_camera_snapshoting_images, start_camera_snaphosting_audio])
    logging.info("Cameras will use: " + ", ".join([func.__name__ for func in funcs]))
    for camera in config.cameras:
        for func in funcs:
            logging.info("Starting thread " + func.__name__)
            loop = asyncio.get_running_loop()
            awaitable = loop.run_in_executor(None, func, camera)


asyncio.run(main())
