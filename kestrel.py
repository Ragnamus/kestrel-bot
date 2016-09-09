import sys
import os
import logging
import traceback
import datetime
import json
from collections import Counter
from discord.ext import commands

ROOT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT_DIR, 'data')

initial_extensions = [
    'cogs.images',
]

# setup log file
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='kestrel.log', encoding='utf-8', mode='w')
log.addHandler(handler)

# args for bot
prefix = '!'
description = """
Hello! This is Kess, your multi-talented utility bot.
"""
help_attrs = dict(hidden=True)

# define bot
bot = commands.Bot(command_prefix=prefix,
                   description=description,
                   pm_help=None,
                   help_attrs=help_attrs)


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()


@bot.event
async def on_resumed():
    print('resumed...')


@bot.event
async def on_command(command, ctx):
    bot.commands_used[command.name] += 1
    message = ctx.message
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)

    log.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message,
                                                                         destination))


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)


def load_credentials():
    with open(os.path.join(DATA_DIR, 'credentials.json')) as f:
        return json.load(f)

if __name__ == '__main__':
    credentials = load_credentials()
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension,
                                                               type(e).__name__,
                                                               e))

    bot.run(credentials['discord_token'])
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)