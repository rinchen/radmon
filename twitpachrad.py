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
X_FEED_ID = 12345
x_api = xively.XivelyAPIClient(X_API_KEY)
x_feed = x_api.feeds.get(X_FEED_ID)

#normally ttyACM0
arduino = serial.Serial('/dev/ttyACM0', 19200)
# for Mac OS X
#arduino = serial.Serial('/dev/tty.usbmodem1d1341', 19200)

# we don't want to spam twitter
twitter_counter = 0

while True:

    # get the data and assemble it
    message = arduino.readline()
    message = message.strip().split(',')
    if args.verbose:
        print "Readline: %s\n" % message

# On Mac OS X, there is a python-readline bug which will often
# produce bogus data on the first pull. Until that bug is fixed
# you'll need to include some sort of fix loop like this:
#    try:
#    #fix readline errors for usv
#        if float(message[0]) < 200:
#            if float(message[1]) > 20:
#                message[1] = str(float(message[1]) / 100)
#            if float(message[2]) > 20:
#                message[2] = str(float(message[2]) / 100)
#        twitter_message = message[0] + ' CPM, ' + message[1] + ' uSv/h, ' \
#            + message[2] + ' AVG uSv/h, ' + message[3] \
#            + ' time(s) over natural radiation'
#        if args.verbose:
#            print "Twitter: %s\n" % twitter_message
#    except:
#        print "Received bogus data"
#        print "%s" % message
#        continue

# This is the original twitter message with all of the data. People will not
# read the web page that describes how to interpret this and will start
# panicking at the "times(s) over natural radiation". Because of this
# we'll default to something less scary. The code is left here for your
# reference.
#        twitter_message = message[0] + ' CPM, ' + message[1] + ' uSv/h, ' \
#            + message[2] + ' AVG uSv/h, ' + message[3] \
#            + ' time(s) over natural radiation'

# High radiation is anything over 100 milirems, aka 1000 uSv so let's
# provide some hopefully helpful commentary on twitter.
# We can use the on-board average to help filter out anomalies.
# There is probably a better way to do this.
#
# Sometimes we get a back packet back resulting in us not having a
# message[2].
    if len(message) > 2:
        usv_reading = float(message[1])
        usv_average = float(message[2])
        interpretation = ""
        if usv_reading <= 1.2:
            interpretation = "(normal range)"
        elif usv_reading > 1.2 and usv_reading <= 250:
            interpretation = "(slightly elevated)"
        elif (usv_reading > 250 and usv_reading <= 499) \
                and (usv_average > 250):
            interpretation = "(Elevated reading)"
        elif (usv_reading > 499 and usv_reading <= 999) \
                and (usv_average > 499):
            interpretation = "(Pre-Alarm! Significantly Elevated.)"
        elif usv_reading > 999 and usv_average > 999:
            interpretation = "(Radiation Alarm! [or the detector is broken])"
        else:
            interpretation = "(Disregard: failed quality control check)"

        twitter_message = message[1] + ' uSv/h ' + interpretation
        if args.verbose:
            print "Twitter: %s\n" % twitter_message

        # send data to twitter every 10 minutes so we don't spam them
        if (twitter_counter >= 10 and not args.noop):
            try:
                __ = twitter_api.PostUpdate(twitter_message)
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
