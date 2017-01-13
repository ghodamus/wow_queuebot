# Queue tracking methods for use by QueueBot.
# Written to track Elysium queue depth in the R&D Discord Server.
# Created by Ghodamus (Mark), January 2017
# User guide in Google Drive: https://goo.gl/3Xv8ib

import datetime,pickle

class track_queue():

	# Entries were originally stored by username instead of user id.
	# This method converts older entries to the proper index.
	def uname_to_uid(self,username,uid):
		if username in self.tracks and uid not in self.tracks:
			self.tracks[uid] = [x for x in self.tracks[username]]
			del self.tracks[username]

	# Method to purge stale (>6hours) avgRuns
	def purgeStaleAvgs(self):
		purgeKeys = []
		for x in self.avgRuns:
			if ((datetime.datetime.now() - x).total_seconds() > 21600):
				purgeKeys.append(x)

		if len(purgeKeys) > 0:
			for x in purgeKeys:
				del self.avgRuns[x]

	# Method for entering new depth-at-time data points.
	# Takes four arguments: user ID, username, user's position in the queue, and an optional field to indicate how delayed the entry is.
	# The optional parameter is the number of minutes late this entry is at the time it is added.
	def addtime(self,uid,username,pos,delaymins=0):
		# Runs a backup if the last one was more than 30 minutes ago.
		if (datetime.datetime.now() - self.backupTimer).total_seconds() > 1800:
			self.runBackup()
			self.backupTimer = datetime.datetime.now()

		# Calculate actual(ish) time of datapoint.
		timenow = datetime.datetime.now() - datetime.timedelta(minutes=delaymins)

		# The first time a uid submits a time, it creates an entry in the tracks{} dict.
		if uid not in self.tracks:
			self.tracks[uid] = [(timenow,pos)]
			print(uid + " added to tracking")
			return "Added to tracking."

		# tracks[uid] can be empty due to undo, clear, or purge.
		elif len(self.tracks[uid]) == 0:
			self.tracks[uid].append((timenow,pos))
			print(uid + " added to tracking.")
			return "Added to tracking."

		# A very basic anti-spamming check.
		elif (datetime.datetime.now() - self.tracks[uid][-1][0]).total_seconds() < 60:
			print('Not enough time between updates.')
			return "Please wait more than 60 seconds between updates."

		# If a new entry is a larger number than the last one recorded, or last post was more than 6 hours ago, assume you're refreshing the queue.
		elif (self.tracks[uid][-1][1] < pos) or ((datetime.datetime.now() - self.tracks[uid][-1][0]).total_seconds() > 21600):
			self.tracks[uid] = [(timenow,pos)]
			print("Tracking reset")
			return "Tracking reset."

		# Main method for valid entries.
		else:
			# Add new entry to existing list of sets.
			self.tracks[uid].append((timenow,pos))

			# If this was an out-of-order entry, get the entries sorted back into order.
			if delaymins > 0:
				self.tracks[uid].sort(key=lambda x: x[0])

			#Do a bunch of math.
			shortPosDelta = self.tracks[uid][-1][1] - self.tracks[uid][-2][1]
			longPosDelta = self.tracks[uid][-1][1] - self.tracks[uid][0][1]
			shortTimeDelta = (self.tracks[uid][-1][0] - self.tracks[uid][-2][0]).total_seconds()
			longTimeDelta = (self.tracks[uid][-1][0] - self.tracks[uid][0][0]).total_seconds()
			
			# shortBurn and longBurn are measured in change per hour.
			shortBurn = int(shortPosDelta / shortTimeDelta * 3600)
			longBurn = int(longPosDelta / longTimeDelta * 3600)

			# Send a copy of the shortburn time for this position to the avgRuns{}
			self.avgRuns[timenow] = (pos,shortBurn)

			# outputs
			print("New position: " + str(pos) +":")
			outval = "Moved " + str(shortPosDelta) + " since last update, rate is " + str(shortBurn) + " users/hour\n"
			outval += "Moved " + str(longPosDelta) + " in total, rate is " + str(longBurn) + " users/hour (global: " + self.findBigAvg() + ")\n"
			outval += "Average speed at your depth: " + self.findSmallAvg(pos)
			print(outval)
			return outval

	# Get the grand average of all avgRuns
	def findBigAvg(self):

		# Avoid dividing by zero. It's bad for you.
		if (len(self.avgRuns) > 0) :
			count = 0
			total = 0

			# Automatically purge any records older than 6 hours.
			self.purgeStaleAvgs()

			for x in self.avgRuns:
				count += 1
				total += self.avgRuns[x][1]

			# If no reports remained after purging...
			if count < 1:
				return "unknown (insufficient reports)"

			# Expected output.
			else:
				return str(int(total / count)) + ' users/hour, based on ' + str(count) + ' reports'

		# If there were no reports in the first place...
		else:
			return "unknown (insufficient reports)"

	# Get the average of runs that ended within a given distance (default 2000) of a base value.
	# Works much like the method above, other than the range restriction.
	def findSmallAvg(self,base,range=2000):
		if (len(self.avgRuns) > 0) :
			count = 0
			total = 0
			bottom = int(base - range / 2)
			if bottom < 0:
				bottom = 0
			top = int(base + range / 2)

			self.purgeStaleAvgs()

			for x in self.avgRuns:
				if self.avgRuns[x][0] <= top and self.avgRuns[x][0] >= bottom:
					count += 1
					total += self.avgRuns[x][1]
			if count < 1:
				return "unknown (insufficient reports)"
			else:
				return str(int(total / count)) + ' users/hour, based on ' + str(count) + ' reports'
		else:
			return "unknown (insufficient reports)"

	# Print wrapper for findBigAvg
	def getBigAvg(self):
		retstring = 'Checking my sources...'
		bigAvg = self.findBigAvg()
		retstring += '\nIn the last 6 hours, average progress rate was ' + bigAvg + "."
		print(retstring)
		return retstring

	# Print wrapper for findSmallAvg
	def getSmallAvg(self,base,range=2000):
		print('Checking my sources for data between ' + str(int(base - range / 2)) + " and " + str(int(base + range / 2)) + "...")
		smallAvg = self.getSmallAvg(base,range)
		print('In the last 6 hours, progress at that depth was ' + smallAvg + '.')

	# Purges and refills the avgRuns{} dict from existing data points.
	def fillAvgRuns(self):
		#First, we clear the current avgRuns{} dict.
		print("Clearing avgRuns...")
		self.avgRuns = {}

		# Next, recalculate values from existing check-ins.
		print("Reloading run data...")

		# Only users with multiple entries can generate deltas.
		for uid in self.tracks:
			if len(self.tracks[uid]) > 1:

				# Grab the earliest entry.
				last = self.tracks[uid][0]

				# Crawl over entries, do calculations, keep track of the one you just processed for comparison.
				for x in self.tracks[uid][1:]:
					timediff = (x[0]-last[0]).total_seconds()
					posdiff = x[1]-last[1]
					self.avgRuns[x[0]] = (x[1],int(posdiff / timediff * 3600))
					last = x

		# Sanity check
		print("Running getBigAvg...")
		self.getBigAvg()

	# Backup routine. Pickles the tracts{} dict; everything else can be recovered from there.
	def runBackup(self):
		print("Running backup.")
		with open('QTBackup.pickle','wb') as outfile:
			pickle.dump(self.tracks,outfile,pickle.HIGHEST_PROTOCOL)
		print("Pickle complete.")

	# Removes the most recent entry for a given user.
	def undoEntry(self,uid):
		print('Deleting most recent entry...')
		if uid not in self.tracks:
			print("Found no entries to delete!")
			return "Found no entries to delete!"
		elif len(self.tracks[uid]) == 0:
			print("Found no entries to delete!")
			return "Found no entries to delete!"
		else:
			lastTime = self.tracks[uid][-1][0]
			if lastTime in self.avgRuns:
				del self.avgRuns[self.tracks[uid][-1][0]]
			del self.tracks[uid][-1]
			lastAge = int((datetime.datetime.now() - lastTime).total_seconds() / 60)
			retval = "Your entry from " + str(lastAge) + " minutes ago has been deleted."
			print(retval)
			return retval

	# Removes all entries for a given user.
	def clearUser(self,uid):
		if uid not in self.tracks:
			print("User not found!")
			return "User not found!"
		elif len(self.tracks[uid]) < 1:
			print("No entries to delete!")
			return "No entries to delete!"
		else:
			self.tracks[uid] = []
			print("All entries cleared.")
			return "All entries cleared."

	# Removes all entries for a user, and recalculates the avgRuns{} dict to remove traces.
	def purgeUser(self,uid):
		print('Initiating purge...')
		self.clearuser(uid)
		self.fillAvgRuns()

	# Generates login ETA based on current trend.
	def eta(self,uid):
		print('Generating ETA.')
		if uid not in self.tracks:
			print('Unable to generate; no tracking data!')
			return 'Unable to generate; no tracking data! Please enter a queue position for yourself with !wowqueue (position)'
		elif len(self.tracks[uid]) == 0:
			print('Unable to generate; no tracking data!')
			return 'Unable to generate; no tracking data! Please enter a queue position for yourself with !wowqueue (position)'
		elif (datetime.datetime.now() - self.tracks[uid][-1][0]).total_seconds() > 21600:
			print('No updates in over 6 hours.')
			return 'Your position in queue has not been updated in over 6 hours.\nPlease update position and try again.'
		else:
			if len(self.avgRuns) == 0:
				print('No avgRuns to calculate on.')
				return 'Unable to calculate; no valid runs reported in the last 6 hours.'

			# Yes, I'm an idiot. My earlier average calculators return strings instead of numbers.
			# I'll fix this eventually. Until then, lots of extra unnecessary code here.
			else:
				count = 0
				total = 0

				# Automatically purge any records older than 6 hours.
				self.purgeStaleAvgs()

				for x in self.avgRuns:
					count += 1
					total += self.avgRuns[x][1]

				# If no reports remained after purging...
				if count < 1:
					print('No avgRuns to calculate on.')
					return 'Unable to calculate; no valid runs reported in the last 6 hours.'

				# Expected output.
				else:
					rate = int(total / count)
					curPos = self.tracks[uid][-1][1]
					secondsDelta =  0 - int(curPos / rate * 3600)
					etaTime = self.tracks[uid][-1][0] + datetime.timedelta(seconds=secondsDelta)
					etaDuration = (etaTime - datetime.datetime.now()).total_seconds()
					outline = 'Based on your previous position at ' + str(curPos) + ', '
					if etaDuration <= 0:
						print('ETA was negative number.')
						outline += 'you should already be in.\n If you are still waiting, please update your queue position.'
					else:
						print('ETA ' + str(int(etaDuration / 3600)) + ' hours, ' + str(int(etaDuration/60) % 60) + ' minutes.')
						outline += 'your ETA is '+ str(int(etaDuration / 3600)) + ' hours, ' + str(int(etaDuration/60) % 60) + ' minutes.'
					return outline

	# Initialization method.
	# For ease of use, can import a dict of track records at creation.
	def __init__(self, trackSeed = {}):
		self.backupTimer = datetime.datetime.now()
		self.avgRuns = {}
		if len(trackSeed) == 0:
			print("Initialized with no prior data.")
			self.tracks = {}
		else:
			print("Initialized with data, populating averages.")
			self.tracks = {x:trackSeed[x] for x in trackSeed}
			self.fillAvgRuns()


