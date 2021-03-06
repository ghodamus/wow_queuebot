# Queue monitoring bot!
# Created by Ghodamus (Mark), January 2017
# User guide in Google Drive: https://goo.gl/3Xv8ib

# I am a simple man, so I just run this from the command line with "python3 QueueBot.py"
# All of the print() statements here are so that I can monitor the console for updates.

print('Warming up the bot.')

# Yes, I probably import more than I need. Some is for plans for later expansion.
import discord,pickle,datetime,QueueTracker,QueueHandler,importlib
from discord.ext import commands

# QueueTracker periodically saves its update history in a pickle. We try to load that pickle here.
print ('Loading seed...')
trackSeed = {}

try:
	with open("QTBackup.pickle","rb") as infile:
		trackSeed = pickle.load(infile)
	print("Found and loaded seed.")
except FileNotFoundError:
	print("Seed not found. Starting from scratch.")

print('Initializing tracker...')
t = QueueTracker.track_queue(trackSeed)

print('Tracker initialized. Now the handler...')
h = QueueHandler.handler(t)

print("Handler's up, now for the client.")
client = discord.Client()

# Monitors for properly formatted messages, then hands off to parser as necessary.
@client.event
async def on_message(message):

	# Case-insensitive, accepts !wowqueue or !wq
	lowContent = message.content.lower()
	if lowContent.startswith('!wowqueue ') or lowContent == '!wowqueue' or lowContent.startswith('!wq ') or lowContent == '!wq':
		
		print(datetime.datetime.now())
		print("Received command from " + message.author.name + " (" + message.author.id + ")")
		try:
			print("Server was " + message.server.name)
		except AttributeError:
			print("Message was sent directly.")

		# Calls the handler object to parse the message.
		# Expected result is a tuple containing two values: message destingation, and message text.
		result = h.parse(message)

		# Responds based on parsed result.
		await client.send_message(result[0],result[1])
		print("\n----------\n")

@client.event
async def on_member_join(member):
	if member.server.name == "Elysium Queuebot":
		print(member.name + " has joined Elysium Queuebot server; sending welcome message.")
		msg = "Welcome to the Elysium Queuebot server! I'm Queuebot.\n"
		msg += "You can send commands to me here or in the #elysium_queue channel.\n"
		msg += 'Type "!wq help" for a list of basic commands, or visit my user manual at https://goo.gl/3Xv8ib\n'
		msg += "Thanks for visiting, and best of luck in the queue!"

		await client.send_message(member,msg)
		print("\n----------\n")

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Systems online!')
    print('\n----------\n')

# Put your client secret in here.
client.run('Discord Client Secret')
