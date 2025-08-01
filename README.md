# XScreenSaver Wayland Enhancement
## Enhanced Blanker and Locker for XScreenSaver on Wayland
[XScreenSaver](https://www.jwz.org/xscreensaver/) is a screen saver collection built for the X11 Window System / X.Org Server. Wayland / Mutter can kind of run XScreenSaver, but some features are missing or unreliable, even if you have XWayland. XScreenSaver will [likely never](https://www.jwz.org/blog/2023/09/wayland-and-screen-savers/) be ported to Wayland. ...Or, [maybe it will](https://www.jwz.org/blog/2025/07/xscreensaver-6-11/).

But I love the silly little hacks, because I have joy in my heart. And I would be OK running a mostly reliable screen locker, because I operate in a mostly secure physical environment, but my company still requires the semblance of machine security. And so I wrote up some hacky scripts to run as hacky services, to make XScreenSaver kind of work a little bit better with GNOME on Wayland.
## What You Get
There are two scripts and services:
1. One that monitors user idleness using the system native idle reporter, and activates the screensaver after a given idle time.
2. And the other that watches for the screenaver to unblank, and then immediately locks the screen using the system's native screen locker.

I have tested this on Fedora 42 and Ubuntu 25.04, with the default builds and environments (GNOME and Wayland). It seems to work well enough to share with other people. I don't know how to write installers, and I don't think I'll bother to learn, so I just kind of describe what to do below.
# Installation
## Get XScreenSaver
Install XScreenSaver
```bash
sudo dnf install '*xscreensaver*'
sudo apt install '*xscreensaver*'
```
### XScreenSaver Version
Starting with version 6.11, XScreenSaver started getting [Wayland support](https://www.jwz.org/blog/2025/07/xscreensaver-6-11/). However, GNOME on Wayland is still unsupported, and now XScreenSaver [just crashes](https://bugzilla.redhat.com/show_bug.cgi?id=2385237). So if you get version 6.11 or later, then you'll need to downgrade to version 6.10 or earlier.

Here is how I did it on Fedora.
```bash
sudo dnf install fedora-repos-archive
sudo dnf list --showduplicates xscreensaver
sudo dnf install xscreensaver-1:6.10.1-1.fc42.x86_64
sudo dnf versionlock add xscreensaver
sudo dnf versionlock list
```
## Get XScreenSaver Wayland Enhancement
Clone this repository.
```bash
git clone https://github.com/pgn674/xscreensaver-wayland-enhancement
cd xscreensaver-wayland-enhancement/
```
## Set Up The Services
Copy the `xscreensaver-wayland-idle-detector.service` and `xscreensaver-wayland-locker.service` files into your local user systemd service place.
```bash
mkdir --parents ~/.config/systemd/user
cp *.service ~/.config/systemd/user/
```
Edit the service files, changing the `ExecStart` lines to have the full paths for wherever you put the `xscreensaver-wayland-idle-detector.py` and `xscreensaver-wayland-locker.py` files.
```bash
vim ~/.config/systemd/user/xscreensaver-wayland-idle-detector.service
vim ~/.config/systemd/user/xscreensaver-wayland-locker.service
```
Enable and start the services.
```bash
systemctl --user daemon-reload
systemctl --user enable xscreensaver-wayland-idle-detector.service
systemctl --user enable xscreensaver-wayland-locker.service
systemctl --user start xscreensaver-wayland-idle-detector.service
systemctl --user start xscreensaver-wayland-locker.service
```
## Configure XScreenSaver
You're going to need to configure XScreenSaver a bit.

Edit the file: `/usr/share/applications/xscreensaver-settings.desktop`

Change:

`Exec=xscreensaver-settings`

To:

`Exec=xscreensaver-settings --display=:0`

Open XScreenSaver settings, and change "Blank After" to 720 minutes.
# Configuration
In addition to not bothering learning how to write an installer, I'm not bothering with any kind of actual proper configuration management system. I told you this thing was hacky, didn't I? So you'll just have to deal with opening the Python files and finding the variables at the top which you can change to your liking.
## Blank After
In `xscreensaver-wayland-idle-detector.py`, see the `idle_blank_time` variable. This defaults to `300000`, and the unit is milliseconds. 300000 milliseconds is 5 minutes. This is how long you will need to be idle for (as detected by the GNOME Mutter idle monitor) before the screen saver will be started. It's meant to act just like XScreenSaver's own "Blank After" option.
## Log Frequency
In `xscreensaver-wayland-idle-detector.py`, see the `log_frequency` variable. This defaults to `60`, and the unit is... kind of seconds, but it's really iterations of a loop. Every time the code loop iterates this many times, some more verbose log messages will be printed.
## Lock Screen After
In `xscreensaver-wayland-locker.py`, see the `lock_screen_after_seconds` variable. This defaults to `60`, and the unit is seconds. 60 seconds is 1 minute. This is the grace period that you get after the screen saver starts, before interrupting the screen saver will result in a locked screen. It's meant to act just like XScreenSaver's own "Lock Screen After" option.
# Limitations
## No Screen Saver When Locked
If the screen gets locked, then the screen saver won't be started again. Sorry, that's just the way it goes. Even if the screen saver got started up, it would just be under the lock screen, and you wouldn't see it. And then when you unlocked the computer, the screen saver would stop, and the script would just lock the screen all over again. It'd be a mess. So it's not done.
# Troubleshooting
## Logs
You can see service statuses and logs this way.
```bash
systemctl --user status xscreensaver-wayland-idle-detector.service
systemctl --user status xscreensaver-wayland-locker.service
journalctl --user --unit xscreensaver-wayland-idle-detector.service
journalctl --user --unit xscreensaver-wayland-locker.service
```
## Manual Run
And you can try just straight up manually running the scripts, to see if there's some other error you can catch.
```bash
./xscreensaver-wayland-idle-detector.py
./xscreensaver-wayland-locker.py
```
