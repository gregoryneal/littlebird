from twilio.rest import Client
import tweepy
import os
import logging
from datetime import datetime
import time
import pprint
from socket import timeout

twilio_number = str(os.environ['PHONE_NUMBER_TWILIO'])
test_phone_number = str(os.environ['PHONE_NUMBER_CELL'])

def sendMessageToNumber(message, number = test_phone_number):
	try:
		message = client.messages.create(to=number, from_=twilio_number, body=message)
		#print(message.sid)
	except Exception:
		print("error sending message")

class MyStreamListener(tweepy.StreamListener): #only listens to tweet streams with a status text, no retweets tweets from other people
	
	def setStreamRef(self, stream):
		self.stream = stream

	def setFollowers(self, followers):
		self.followers = followers

	def on_status(self, status):
		user = getattr(status, 'user')
		userId = getattr(user, 'id_str')
		#pprint.pprint(status._json)
		isEmptyRetweet = hasattr(status, 'retweeted_status') #catches retweets with no added tweet message
		#print(str(isEmptyRetweet))
		isSelfTweet = userId in self.followers #makes sure the tweet came from the right account instead of someone @tagging them
		#print(str(isSelfTweet))
		if not isEmptyRetweet and isSelfTweet:
			createTime = datetime.now() #returns a datetime object
			print(createTime.strftime('%I:%M%p') + " ->@" + user.screen_name + ":")
			lines = status.text.split('\n')
			for line in lines:
				if line.strip() == '':
					continue			
				print("\t-> " + line.strip())
			print()
			sendMessageToNumber('\n@'+user.screen_name+':\n'+status.text)
		elif isEmptyRetweet and isSelfTweet: #they just retweeted something but didn't add anything else
			self.retweetsCaught += 1
			#print("Retweet #"+str(self.retweetsCaught))
		elif not isSelfTweet:  #someone else just tweeted this and @tagged the person in it
			self.tweetsFromOthers += 1
			#print("Tweets from others #"+str(self.tweetsFromOthers))

			if not isEmptyRetweet: #someone just retweeted the person and added their own status to it
				self.retweetsCaught += 1
				#print("Retweeted quote detected: #"+str(self.retweetsCaught))

		#self.stream.disconnect()

	def on_connect(self):
		self.retweetsCaught = 0
		self.tweetsFromOthers = 0
		#print("Connected to users twitter feed:")
		print('\\')
		print('\\..')
		print()

if __name__ == "__main__":

	tck = str(os.environ['TWITTER_CONSUMER_KEY'])
	tcs = str(os.environ['TWITTER_CONSUMER_SECRET'])
	tt = str(os.environ['TWITTER_ACCESS_TOKEN_LITTLEBIRD'])
	ts = str(os.environ['TWITTER_ACCESS_SECRET_LITTLEBIRD'])

	client = Client() #twilio key and secret are stored as environment variables

	twapi = tweepy.OAuthHandler(tck, tcs)
	twapi.set_access_token(tt, ts)
	api = tweepy.API(twapi)

	follow = ['25073877'] #donald trump @realDonaldTrump
	#follow.append('881323567941603328') #my twitter @littlebirddev

	listener = MyStreamListener()
	stream = tweepy.Stream(twapi, listener)
	listener.setStreamRef(stream)
	listener.setFollowers(follow)

	users = [api.get_user(int(str_id)).screen_name for str_id in follow]
	print("Getting tweets from users: @" + str(', @'.join(users)))
	print("Sending text notifications to: " + test_phone_number)

	while True:
		try:
			stream.filter(follow)
		except (KeyboardInterrupt, MemoryError, SystemExit) as e:
			#need a way to exit the loop
			print("Exiting with code: " + type(e).__name__)
			stream.disconnect()
			break
		except Exception as e:
			print("Streaming Error: ")
			print()
			logging.exception()
			print()
			print("Restarting stream...")
			stream.disconnect()