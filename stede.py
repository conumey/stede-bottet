import asyncio
import os
import discord
import humanize
from aiopyarr.models.host_configuration import PyArrHostConfiguration
from aiopyarr.radarr_client import RadarrClient
from aiopyarr.sonarr_client import SonarrClient
from aiopyarr.readarr_client import ReadarrClient

import logging
import logging.handlers
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    'stede.log', maxBytes=(1048576*5), backupCount=7
)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())
global filmChannel
global tvChannel

#info clients
SONARRHOST = os.getenv('SONARR_HOST')
SONARRKEY = os.getenv('SONARR_KEY')
sonarrHostConfig = PyArrHostConfiguration(ipaddress=SONARRHOST, api_token=SONARRKEY, port=80)

RADARRHOST = os.getenv('RADARR_HOST')
RADARRKEY = os.getenv('RADARR_KEY')
radarrHostConfig = PyArrHostConfiguration(ipaddress=RADARRHOST, api_token=RADARRKEY, port=80)

READARRHOST = os.getenv('READARR_HOST')
READARRKEY = os.getenv('READARR_KEY')
readarrHostConfig = PyArrHostConfiguration(ipaddress=READARRHOST, api_token=READARRKEY, port=80)

READARR2HOST = os.getenv('READARR2_HOST')
READARR2KEY = os.getenv('READARR2_KEY')
readarr2HostConfig = PyArrHostConfiguration(ipaddress=READARR2HOST, api_token=READARR2KEY, port=80)

@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord.')
    task = asyncio.create_task(checkStats(), name='check stats')

async def checkStats():
    while(True):
        queue = 0
        animeseries = 0
        animeepisodes = 0
        tvseries = 0
        tvepisodes = 0
        missingeps = 0
        movies = 0
        missingFilms = 0
        upcomingFilms = 0
        notavailable = 0
        freespace = 0
        totalspace = 0

        logger.debug('Updating stats:')
        logger.debug('Polling Sonarr...')
        try:
            async with SonarrClient(sonarrHostConfig) as sonarr:
                fs = await sonarr.async_get_diskspace()
                freespace = fs[2].freeSpace
                totalspace = fs[2].totalSpace
                animeepisodes = len(await sonarr.async_get_filesystem_media("/anime"))
                tvepisodes = len(await sonarr.async_get_filesystem_media("/tv"))
                queue += (await sonarr.async_get_queue_status()).count
                missingeps = len((await sonarr.async_get_wanted(include_series=False, page_size=1000)).records)
        except Exception as err:
            logger.debug(err)

        logger.debug('Polling Radarr...')
        try:
            async with RadarrClient(radarrHostConfig) as radarr:
                movies = len(await radarr.async_get_filesystem_media("/movies"))
                queue += (await radarr.async_get_queue_status()).count
                all = await radarr.async_get_movies()
                movies = len(all)
                missingFilms = len([x for x in all if x.hasFile == False & x.isAvailable == True])
                upcomingFilms = len([x for x in all if x.isAvailable == False])
        except Exception as err:
            logger.debug(err)

        await client.get_channel(1018671999230419036).edit(name=f'Films: {movies}')
        await client.get_channel(1018673245039378452).edit(name=f'TV Episodes: {tvepisodes}')
        await client.get_channel(1018675597330886726).edit(name=f'Anime Episodes: {animeepisodes}')
        await client.get_channel(1018675679887364177).edit(name=f'Avail: {humanize.naturalsize(freespace)} / {humanize.naturalsize(totalspace)}')

        await asyncio.sleep(35)

client.run(TOKEN)


