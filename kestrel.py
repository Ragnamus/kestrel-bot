"""
KESTREL_BOT: A discord bot loosely based off https://github.com/Cog-Creators/Red-DiscordBot

Authors: Matthew Truscott (matthew.a.truscott@gmail.com)
"""

import sys
import os
import logging
import traceback
import datetime
import json
from collections import Counter
from discord.ext import commands
import discord
import cogs.utils.sortinghat as ush
import cogs.background as bg

"""
Credentials for accessing certain APIs
"""
def load_credentials():
    with open(os.path.join(CREDENTIALS_DIR, 'credentials.json')) as f:
        return json.load(f)

"""
Persistence information for the bot. Currently stores a message counter so that messages are logged into new files
TODO: store messages more tidily (currently creates a new log file regardless of length of previous one when bot is
started
"""
def load_persistence():
    with open(os.path.join(DATA_DIR, 'persistence.json'), 'r+') as f:
        pers_dict = json.load(f)
        int_message = int(pers_dict['message_count'])
        int_message += 1
        pers_dict['message_count'] = "%i" % (int_message)
        f.seek(0)
        json.dump(pers_dict, f, indent=4)
        f.truncate()

        return pers_dict


ROOT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
MESSAGE_DIR = os.path.join(ROOT_DIR, 'message')
CREDENTIALS_DIR = os.path.join(ROOT_DIR, '.credentials')
JSON_LIMIT = 1000
JSON_COUNTER = 0
persistence = load_persistence()
JSON_MESSAGE = int(persistence['message_count'])
message_dict = {}
RECORD_MESSAGES = True


# bot is modular, see cogs for special commands
initial_extensions = [
    'cogs.core', 'cogs.modactions', 'cogs.report'
]

# setup log file
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='kestrel.log', encoding='utf-8', mode='w'
)
log.addHandler(handler)

# args for bot
prefix = 'k.'
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
        print('{0.__class__.__name__}: {0}'.format(
            error.original), file=sys.stderr
        )


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

    log.info('{0.timestamp}: {0.author.name} in {1}:'
             '{0.content}'.format(message, destination))


@bot.event
async def on_message(message):
    # if not message.author.bot:
    #     if RECORD_MESSAGES:
    #         global JSON_COUNTER
    #         global JSON_MESSAGE
    #         global message_dict
    #
    #         if JSON_COUNTER < JSON_LIMIT:
    #             JSON_COUNTER += 1
    #             #persistence['index'] = "%i" % (JSON_COUNTER)
    #
    #         else:
    #             JSON_COUNTER = 0
    #             #persistence['index'] = "%i" % (JSON_COUNTER)
    #
    #             JSON_MESSAGE += 1
    #             persistence['message_count'] = "%i" % (JSON_MESSAGE)
    #
    #             per_path = os.path.join(DATA_DIR, 'persistence.json')
    #             with open(per_path, 'w') as fp:
    #                 json.dump(persistence, fp)
    #
    #             path = os.path.join(MESSAGE_DIR,
    #                                 'messagelog%i.json' % (JSON_MESSAGE))
    #             with open(path, 'w+') as fl:
    #                 json.dump(message_dict, fl)
    #             message_dict = {}
    #
    #         entry = "entry-%i-%i" % (JSON_MESSAGE, JSON_COUNTER)
    #         message_dict[entry] = {
    #             "channel": message.channel.name,
    #             "timestamp": str(message.timestamp),
    #             "author": message.author.name,
    #             "contents": message.content
    #         }
    #         path = os.path.join(MESSAGE_DIR,
    #                             'messagelog%i.json' % (JSON_MESSAGE))
    #         with open(path, 'w+') as fl:
    #             json.dump(message_dict, fl)
    # else:
    #     return


    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    print("%s joined the server" % (member.name))

    with open(os.path.join(DATA_DIR, 'userbase.json'), 'r+') as f:
        data = json.load(f)

        userExists = False
        for key, value in data.items():
            if key == member.id:
                data[member.id]["alive"] = True
                userExists = True
        if not userExists:
            # add user data
            data[member.id] = {
                "name": member.name,
                "isbot": member.bot,
                "avatar": member.avatar_url,
                "created": member.created_at.strftime("%Y, %B %d"),
                "display name": member.display_name,
                "joined at": member.joined_at.strftime("%Y, %B %d"),
                "alive": True
            }

            # first time joining! deploy care package
            await bot.send_message(member, 'Hi! Welcome to the server. To get started, click on this link: '
            'https://goo.gl/forms/2Fq6Pnvab9DUCJWB2. When you have completed the survey, reply to this message with'
            ' "k.sort". Thank you for your time.')


        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()


@bot.event
async def on_member_remove(member):
    print("%s left the server" % (member.name))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-w':
            RECORD_MESSAGES = True

    credentials = load_credentials()
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(
                extension, type(e).__name__, e)
            )

    bot.loop.create_task(bg.background_main(bot))
    bot.run(credentials['discord_token'])
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
