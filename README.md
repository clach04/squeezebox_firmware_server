# squeezebox_firmware_server

Fake Logitech SqueezeBox / Smart Radio EA Firmware Server

WARNING this could brick your device, see LICENSE.

Use at your own risk.

Originally written for https://forums.slimdevices.com/forum/user-forums/squeezebox-radio/1679073-factory-reset-stuck-logitech-ue-smart-radio?p=1681965#post1681965

For most uses cases this script/tool is NOT needed.
Instead rely on the Logitech server and/or your [local LMS / Logitech Media Server / SlimServer / SqueezeCenter / Squeezebox Server](https://github.com/LMS-Community/slimserver).

Regular firmware update options/instructions:
  * https://lms-community.github.io/reference/custom-firmware/
  * community firmware locatin https://sourceforge.net/projects/lmsclients/files/squeezeos/

If that's not possible for any reason this maybe a solution.

## Overview

It looks like (luckily) all traffic is http and NOT https so no need to
worry about proxies, certificates, encryption, etc.

If the hostname for `config.logitechmusic.com` is hacked (however you want to
do that, e.g. edit your DNS server or simple ssh into the squeezebox and
edit `/etc/hosts`) then you can serve up your own json payload.

From my experiments with a device with firmware 10.1.0 r16977 the config
server is queried with both the MAC address and the firmware revision.
I did try a web server briefly but with the colons present and the query
parameter I found it easier to write a hacky-script to always return the
json I want (without ANY firmware checks) whatever the URL requested is
with the exception of a firmware download request (i.e. use the same
server for both the json and the firmware).

One obvious alternative would be to call/follow the lua code (or run the
extract manually) with a locally scp'd firmware.bin (i.e. trace through
`UpgradeUBI.lua`).

Enabling ssh to edit /etc/host is NOT covered here, consult:

  * https://lms-community.github.io/reference/enable-ssh/
  * https://forums.slimdevices.com/forum/user-forums/


## Usage

This is both a Python 3 and Python 2 script. It should work with any version of Python 2.7+.

This starts a web server on port 80.

Under Microsft Windows the only thing to worry about is whether another
server is already listening on port 80.

Under Linux/Unix/Mac 80 is a reserved port and either need to delagate
permission for the port or run as root with all the warnings that go
along with that.

The server is HARD CODED to return a payload, the only way to change
this is to edit the source code. The one exception is the name on the
file system to serve, it defaults to firmware.bin but can be override
via Operating System variable `FIRMWARE_FILENAME`.
NOTE the server ALWAYS serves the filename to the client as `firmware.bin`.

To start, ensure you have the firmware.bin present in the same directory
as this README.md and the python script.

Then try ONE of:

    python fake_logitech_server.py
    python2 fake_logitech_server.py
    python3 fake_logitech_server.py
    py -2 fake_logitech_server.py
    py -3 fake_logitech_server.py

As a sanity check check the server using a web browser, curl, or wget. On the radio there is likely ONLY wget.
For example in a web browser on the server machine open http://localhost

On squeezebox, assuming host/dns is updated to your server:

    wget -O -  http://config.logitechmusic.com

Further sanity check is to pull down the firmware to make sure it's all present.

Then re-initiate the firmware update on the radio.

If already connected via ssh, monitor progress in /var/log/messages, e.g.:

    tail -f /var/log/messages
