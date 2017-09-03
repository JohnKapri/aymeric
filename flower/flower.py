import discord
from discord.ext import commands
from random import randint
from .utils.dataIO import dataIO
import random
import datetime
import time
import os
import asyncio
import numpy
from .utils.dataIO import fileIO
from .utils import checks
from __main__ import send_cmd_help

prefix = fileIO("data/red/settings.json", "load")['PREFIXES']

class Flower:
    """Nadeko Flower Generation. Aber mit einem Tai-Twist lol."""

    def __init__(self, bot):
        self.bot = bot
        self.currentFlower = 0
        self.messages_cache = []
        self.scores = dataIO.load_json('data/flower/scores.json')

    @commands.command(pass_context=True, no_pm=True, name='howlong')
    async def howlong(self, context, user: discord.Member):
        """This will get when a given user joined"""
        server = context.message.server
        date = user.joined_at

        if context.message == 'mydick':
            await self.bot.say('Not as long as mine. Lol.')
            return

        await self.bot.say('User ' + user.display_name + ' joined at ' + date.strftime('%d.%m.%Y - %H:%m:%S'))


    @commands.command(pass_context=True, no_pm=True, name='flowertop', aliases=['ftop'])
    async def flowertop(self, context):
        """This will show the top hunters on this server"""
        server = context.message.server
        if server.id in self.scores:
            p = self.scores[server.id]
            scores = sorted(p, key=lambda x: (p[x]['total']), reverse=True)
            message = '```\n{:<4}{:<8}{}\n\n'.format('#', 'TOTAL', 'USERNAME')
            for i, hunter in enumerate(scores, 1):
                if i > 10:
                    break
                message += '{:<4}{:<8}{}\n'.format(i, p[hunter]['total'], p[hunter]['author_name'])
            message += '```'
        else:
            message = '**Please shoot something before you can brag about it.**'
        await self.bot.say(message)

    async def _save_scores(self):
        dataIO.save_json('data/flower/scores.json', self.scores)

    async def _generate_flower(self, message):
        text = message.content
        channel = message.channel
        server = message.server
        user = message.author

        if user.bot:
            return

        curr_time = time.time()
        if float(curr_time) >= 120 and not any(text.startswith(x) for x in prefix) and self.currentFlower == 0:
            if numpy.random.uniform() < 0.02:
                imgfile = random.choice(os.listdir('data/flower/images'))
                imgfile = 'data/flower/images/' + imgfile
                self.currentFlower = 1
                self.messages_cache.append(await self.bot.send_file(channel, imgfile))
                await asyncio.sleep(0.2)
                self.messages_cache.append(await self.bot.send_message(channel, 'A wild Aymeric Flower appeared! Type \'>pick\'!'))

        if self.currentFlower == 1 and message.content.split(' ')[0] == '>pick':
            self.currentFlower = 0
            await self.add_score(server, user)
            self.messages_cache.append(await self.bot.send_message(channel, 'You did it! ' + user.name))
            self.messages_cache.append(await self.bot.send_message(channel, 'You will get 20 credits! (if you have a bank account)'))
            self.messages_cache.append(message)
            await asyncio.sleep(2)
            await self.bot.delete_messages(self.messages_cache)
            self.messages_cache = []

    async def add_score(self, server, user):
        if server.id not in self.scores:
            self.scores[server.id] = {}
        if user.id not in self.scores[server.id]:
            self.scores[server.id][user.id] = {}
            self.scores[server.id][user.id]['total'] = 0
            self.scores[server.id][user.id]['author_name'] = ''
        self.scores[server.id][user.id]['author_name'] = user.display_name
        self.scores[server.id][user.id]['total'] += 1
        await self._save_scores()
        await self._give_chat_credit(user, server)

    async def _give_chat_credit(self, user, server):
        try:
            bank = self.bot.get_cog('Economy').bank
            if bank.account_exists(user):
                bank.deposit_credits(user, 20)
        except:
            pass


def check_folder():
    if not os.path.exists('data/flower'):
        print('Creating data/flower folder...')
        os.makedirs('data/flower')

def check_files():
    f = 'data/flower/scores.json'
    if not dataIO.is_valid_json(f):
        print('Creating empty scores.json...')
        dataIO.save_json(f, {})

def setup(bot):
    check_folder()
    check_files()
    n = Flower(bot)
    bot.add_listener(n._generate_flower, "on_message")
    bot.add_cog(n)
