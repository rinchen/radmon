#!/usr/bin/python3
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
import configparser


def readconfigfile(configfile):
    """read in cofiguration file"""
    config = configparser.ConfigParser()
    try:
        config.read(configfile)
    except configparser.Error as err:
        print(("Config File Error", err))
        exit(1)
    return config


def main():
    "main function"

    # twitter
    encoding = None
    consumer_key = config.get("Twitter", "consumer_key")
    consumer_secret = config.get("Twitter", "consumer_secret")
    access_token_key = config.get("Twitter", "access_token_key")
    access_token_secret = config.get("Twitter", "access_token_secret")

    twitter_api = twitter.Api(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_token_key,
        access_token_secret=access_token_secret,
        input_encoding=encoding,
    )

    # Arduino Serial port
    arduino_serial = config.get("Arduino", "serial")
    arduino_baud = config.get("Arduino", "baud")
    arduino = serial.Serial(arduino_serial, arduino_baud)

    # we don't want to spam twitter
    twitter_counter = 0

    while True:

        # get the data and assemble it
        message = arduino.readline().decode("utf-8").rstrip()
        message = message.split(",")
        if args.verbose:
            print(("Readline: %s\n" % message))

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
        #        twitter_message = message[0] + ' CPM, ' \
        #               + message[1] + ' uSv/h, ' \
        #               + message[2] + ' AVG uSv/h, ' + message[3] \
        #               + ' time(s) over natural radiation'
        #        if args.verbose:
        #            print "Twitter: %s\n" % twitter_message
        #    except:
        #        print "Received bogus data"
        #        print "%s" % message
        #        continue

        # This is the original twitter message with all of the data.
        # People will not
        # read the web page that describes how to interpret this and will start
        # panicking at the "times(s) over natural radiation". Because of this
        # we'll default to something less scary. The code is left here for your
        # reference.
        #        twitter_message = message[0] + ' CPM, ' \
        #            + message[1] + ' uSv/h, ' \
        #            + message[2] + ' AVG uSv/h, ' + message[3] \
        #            + ' time(s) over natural radiation'

        # High radiation is anything over 100 milirems, aka 1000 uSv so let's
        # provide some hopefully helpful commentary on twitter.
        # We can use the on-board average to help filter out anomalies.
        # There is probably a better way to do this.
        #
        # Sometimes we get a back packet back resulting in us not having a
        # message[2]. And sometimes we just get a bad readline.

        if len(message) == 4:
            try:
                usv_reading = float(message[1])
                usv_average = float(message[2])
                float(message[0])
                float(message[3])
            except:
                print(("1:Malformed readline: %s" % (message)))
            else:
                interpretation = ""
                if usv_reading == 0:
                    print(("2:Malformed readline: %s" % (message)))
                    continue
                elif usv_reading <= 1.2:
                    interpretation = "(normal range)"
                elif usv_reading > 1.2 and usv_reading <= 250:
                    interpretation = "(slightly elevated)"
                elif (usv_reading > 250 and usv_reading <= 499) and (usv_average > 250):
                    interpretation = "(Elevated reading)"
                elif (usv_reading > 499 and usv_reading <= 999) and (usv_average > 499):
                    interpretation = "(Pre-Alarm! Significantly Elevated.)"
                elif usv_reading > 999 and usv_average > 999:
                    interpretation = "(Radiation Alarm! [or the detector is broken])"
                else:
                    interpretation = "(Disregard: failed quality control check)"

                twitter_message = str(message[1]) + " uSv/h " + interpretation
                if args.verbose:
                    print(("Twitter: %s\n" % twitter_message))

                # send data to twitter every 10 minutes so we don't spam them
                if twitter_counter >= 10 and not args.noop:
                    try:
                        __ = twitter_api.PostUpdate(twitter_message)
                    except:
                        print(
                            (
                                "Twitter error: %s, Message: %s"
                                % (sys.exc_info()[0], twitter_message)
                            )
                        )
                    else:
                        twitter_counter = 0

            twitter_counter += 1
        else:  # len(message)
            print(("3:Malformed readline: %s" % (message)))

        # sleep for 1 minute
        time.sleep(60)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Receive Radiation" " data from arduino and post to" " twitter."
    )
    parser.add_argument(
        "-n",
        "--noop",
        action="store_true",
        dest="noop",
        help="""Do not post data online. Use with -v""",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="""Extra output regarding received values.""",
        default=False,
    )
    args = parser.parse_args()

    configfile = "twitpachrad.ini"

    config = readconfigfile(configfile)

    main()
