radmon
======

Radiation Monitor Software

This software is for the [Libelium](http://www.libelium.com/) made [Radiation Sensor Board](http://www.cooking-hacks.com/index.php/pack-radiation-sensor-board-for-arduino-geiger-tube.html) for Arduino. 

This repository contains the code for both the Arduino (.pde) as well as the host computer (.py).

The python program receives data from the Arduino and reports the values to both Twitter and Xively (nee Cosm, nee Pachube). The values are collected once every minute and published to Xively. Every 10 minutes a reading is sent to Twitter. (We don't want to spam Twitter.) The Arduino's on-board code keeps track of the real-time running average.
