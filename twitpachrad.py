#!/usr/bin/python
# Joey Stanford
# radation board upload
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.

import twitter
import serial
import time
import sys
import argparse
import xively

parser = argparse.ArgumentParser(description='Receive Radiation'
                                 ' data from arduino and post to'
                                 ' twitter and xively.')
parser.add_argument("-n", "--noop", action="store_true", dest="noop",
                    help='''Do not post data online. Use with -v''',
                    default=False)
parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                    help='''Extra output regarding received values.''',
                    default=False)
args = parser.parse_args()

# twitter
encoding = None
consumer_key = ''
consumer_secret = ''
access_token_key = ''
access_token_secret = ''

twitter_api = twitter.Api(consumer_key=consumer_key,
                          consumer_secret=consumer_secret,
                          access_token_key=access_token_key,
                          access_token_secret=access_token_secret,
                          input_encoding=encoding)

# xively
X_API_KEY = ""
X_FEED_ID = 30643
x_api = xively.XivelyAPIClient(X_API_KEY)
x_feed = x_api.feeds.get(X_FEED_ID)

#arduino = serial.Serial('/dev/tty.usbmodem1d1341', 19200)
arduino = serial.Serial('/dev/ttyACM0', 19200)
#normally ttyACM0

# we don't want to spam twitter
twitter_counter = 0

while 1:

    # get the data and assemble it
    message = arduino.readline()
    message = message.strip().split(',')
    if args.verbose:
        print "Readline: %s\n" % message

    try:
    # sometimes on the first pull we get bogus data
    #fix realine errors for usv
        if float(message[0]) < 200:
            if float(message[1]) > 20:
                message[1] = str(float(message[1]) / 100)
            if float(message[2]) > 20:
                message[2] = str(float(message[2]) / 100)
        twitter_message = message[0] + ' CPM, ' + message[1] + ' uSv/h, ' \
            + message[2] + ' AVG uSv/h, ' + message[3] \
            + ' time(s) over natural radiation'
        if args.verbose:
            print "Twitter: %s\n" % twitter_message
    except:
        print "Received bogus data"
        print "%s" % message
        continue

    # send data to twitter every 10 minutes so we don't spam them
    if (twitter_counter >= 10 and not args.noop):
        try:
            status = twitter_api.PostUpdate(twitter_message)
        except:
            print "Twitter error", sys.exc_info()[0]
        else:
            twitter_counter = 0

    #send data to xively
    if not args.noop:
        try:
            x_feed.datastreams = [
                xively.Datastream(id='CPM', current_value=message[0]),
                xively.Datastream(id='USV', current_value=message[1]),
                xively.Datastream(id='USVAVG', current_value=message[2]),
                xively.Datastream(id='X', current_value=message[3]),
            ]
            x_feed.update()
        except:
            print "Xively error:", sys.exc_info()[0]

    twitter_counter += 1
    # sleep for 1 minute
    time.sleep(60)
