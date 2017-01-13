# Input handler for QueueBot
# Created by Ghodamus (Mark), January 2017
# User guide in Google Drive: https://goo.gl/3Xv8ib

# This class creates an object that parses and responds to messages from QueueBot.
# Most of the processing work is done by a track_queue object from QueueTracker.

import discord

class handler():

	
	# Initialization method.
	# Requers a track_queue object from QueueTracker.
	def __init__(self,tracker):
		self.t = tracker
		# List of IDs of people who should be able to execute admin commands in the bot.
		self.admins = []



	# ---------- BEGIN COMMAND HANDLERS ----------
	#
	# Unless otherwise noted, all handlers take the triggering message as input, and
	# return a tuple containing the message target and message text.

	# Responds to any messages that weren't properly recognized.
	def invalid_command(self,message):
		print('Invalid command.')
		msg = "{0.author.mention} Sorry, didn't get that. Type !wowqueue help for a command list.".format(message)
		target = message.author
		return target,msg

	# Sends a list of commonly-used commands to the requesting user.
	def help_commands(self,message):
		print("Sending command list.")
		target = message.author
		msg = "Some useful commands for Queuebot. Full command list available at https://goo.gl/3Xv8ib\n"
		msg += "Commands are case-insensitive, and you can use !wq in place of !wowqueue for convenience.\n\n"
		msg += "!wowqueue (pos) - Tracks your position in the queue. Replace (pos) with your queue position (for example, '!wowqueue 1000').\n"
		msg += "NOTE: If your new position is larger than your old one or you haven't updated in more than 6 hours, your tracking will be reset.\n"
		msg += "!wowqueue stats - Shows average queue speed over the last 6 hours, based on user reports.\n"
		msg += "!wowqueue eta - Gives ETA to login, based on your last known position."
		return target,msg

	# Allows the user to undo their last update.
	def undo_post(self,message):
		print("Starting undo process.")
		target = message.author
		msg_text = "Deleting last entry for {0.author.mention}...\n"
		msg_text += self.t.undoEntry(message.author.id)
		msg = msg_text.format(message)
		return target,msg

	# Allows a user to clear all of their previous position updates.
	def clear(self,message):
		print("Clearing entries for user.")
		target = message.author
		msg_text = "Clearing all entries for {0.author.mention}...\n"
		msg_text += self.t.clearUser(message.author.id)
		msg = msg_text.format(message)
		return target,msg

	# Method that lets a user update their position in the queue.
	# Takes as argument the source message and the user's reported position.
	def add_time(self,message,posval):
		print("Adding time entry.")
		target = message.author
		msg_text = "Info for {0.author.mention}, now at " + str(posval) + "\n"
		msg_text += self.t.addtime(message.author.id,message.author.name,posval)
		msg = msg_text.format(message)
		return  target,msg 

	# Admin command to force a backup of checkins.
	def safe(self,message):
		self.t.runBackup()
		msg = "Backup complete."
		target = message.author
		return target,msg 

	# Generates queue movement stats for the last 6 hours.
	def stats(self,message):
		print("Generating stats.")
		target = message.channel
		msg = self.t.getBigAvg()
		return target,msg

	# Handles triggers without additional arguments.
	def ping(self,message):
		print("Got a ping.")
		target = message.channel
		msg = 'Queuebot is online! Type "!wowqueue help" for a list of commands.'
		return target,msg

	# Sends the requesting user their ETA, based on last reported position and current progress rate.
	def eta(self,message):
		print('Calculating ETA.')
		target = message.author
		msg_text = 'Calculating ETA for {0.author.mention}:\n'
		msg_text += self.t.eta(message.author.id)
		msg = msg_text.format(message)
		return target,msg


	# ---------- END COMMAND HANDLERS ----------

	# Main parsing method.
	# Takes a triggering message as argument.
	# Based on message content, hands off to a command handlers.
	def parse(self,message):
		print('Parser is running.')

		# Cleanup command to make sure old users that were stored by username are correctly stored by user id.
		self.t.uname_to_uid(message.author.name,message.author.id)

		# First, split up the input content.
		inputList = message.content.split(' ')

		# See if our argument is a number (which would mean a position update request)
		try:
			posval = int(inputList[1])

		# If there was no argument, we know it's a ping request.
		except IndexError:
			return self.ping(message)

		# If we can't cast the argument to int(), then we know it's a text argument.
		except ValueError:

			# We only accept 0 or 1 arguments.
			if len(inputList) != 2:
				return self.invalid_command(message)

			# A bunch of elif statements for each valid text command.
			# We check for message.author.id in admins to validate authorization for admin commands.
			elif inputList[1] == "safe" and message.author.id in self.admins:
				return self.safe(message)
			elif inputList[1] == "help":
				return self.help_commands(message)
			elif inputList[1] == "stats":
				return self.stats(message)
			elif inputList[1] == "undo":
				return self.undo_post(message)
			elif inputList[1] == 'clear':
				return self.clear(message)
			elif inputList[1] == 'eta':
				return self.eta(message)
			# If we got this far, it wasn't a valid command.
			else:
				return self.invalid_command(message)

		# If we successfully cast as int, call the position update command handler.
		else:
				return self.add_time(message,posval)