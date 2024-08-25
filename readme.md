## Dead Simple CCTV
Dead simple cctv recording using python and FFMPEG saving videos to fs.

Record multiple CCTV feeds and save snapshots to kafka queues.
Kafka usage is completly optional.

## Setup
- Run ``docker-compose up -d``
- Edit config file adding cameras and optional kafka setup
- Restart container running again ``docker-compose up -d``

Would like to get more feedback from CCTV feeds, checkout cctv_analytics project.