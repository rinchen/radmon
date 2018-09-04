radmon
======

Radiation Monitor Software

This software is for the [Libelium](http://www.libelium.com/) made [Radiation Sensor Board](http://www.cooking-hacks.com/index.php/pack-radiation-sensor-board-for-arduino-geiger-tube.html) for Arduino.

This repository contains the code for both the Arduino (.pde) as well as the host computer (.py).

The python program receives data from the Arduino and reports the values to Twitter. The values are collected once every minute. They used to be published to Xively with alerting but Xively no longer does what it used to so that code has been removed. Every 10 minutes a reading is sent to Twitter. (We don't want to spam Twitter.) The Arduino's on-board code keeps track of the real-time running average.

For full details, please visit <https://rinchen.github.io/radmon/>.
