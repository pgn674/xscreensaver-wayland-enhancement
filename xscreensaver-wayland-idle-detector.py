#!/bin/env python3

idle_blank_time = 300000
log_frequency = 60

import subprocess, re, time

# Get the current idle time from GNOME Mutter.
def idle_time(do_log):
	idle_monitor_time = 0
	idle_pattern = re.compile(r"^\(uint64 ([0-9]+),\)$")
	process_gdbus = subprocess.Popen(
		["/usr/bin/gdbus", "call", "--session", "--dest", "org.gnome.Shell", "--object-path", "/org/gnome/Mutter/IdleMonitor/Core", "--method", "org.gnome.Mutter.IdleMonitor.GetIdletime"],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)
	process_gdbus.wait()
	for line_gdbus in process_gdbus.stdout:
		match_idle_time = idle_pattern.search(line_gdbus)
		if match_idle_time:
			idle_monitor_time = int(match_idle_time.group(1))
			if do_log % log_frequency == 0: print(f"Idle time is {idle_monitor_time} ms.", flush=True)
	return idle_monitor_time

# See if something is inhibiting idle detection.
def is_idle_inhibited(do_log):
	inhibited = False
	inhibit_pattern = re.compile(r"\([^\(\)]*idle[^\(\)]*\)$")
	process_inhibit_list = subprocess.Popen(
		["gnome-session-inhibit", "--list"],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)
	process_inhibit_list.wait()
	for line_session_inhibit in process_inhibit_list.stdout:
		match_inhibit = inhibit_pattern.search(line_session_inhibit)
		if match_inhibit:
			inhibited = True
			if do_log % log_frequency == 0: print(f"Idle long enough, but screen saver is being inhibited: {line_session_inhibit}", flush=True)
	return inhibited

# See if a screen saver is currently running.
def is_screensaver_running(do_log):
	screensaver_is_running = False
	process_xscreensaver = subprocess.Popen(
			["/usr/bin/xscreensaver-command", "--time"],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)
	process_xscreensaver.wait()
	if do_log % log_frequency == 0: print(f"Got XScreenSaver command return code: {process_xscreensaver.returncode}", flush=True)
	if process_xscreensaver.returncode == 1:
		print("The XScreenSaver command is not working. Restarting idle detection service.", flush=True)
		# Something has gone wrong. I don't know what. But restarting the script seems to fix it.
		subprocess.run(["/usr/bin/systemctl", "--user", "restart", "xscreensaver-wayland-idle-detection.service"])
	for line_xscreensaver in process_xscreensaver.stdout:
		if do_log % log_frequency == 0: print(f"{line_xscreensaver}", flush=True)
		if "screen blanked since" in line_xscreensaver:
			screensaver_is_running = True
	return screensaver_is_running

# Get the current session's session number.
def get_session_number(do_log):
	session_number = -1
	process_loginctl_list_sessions = subprocess.Popen(
		["loginctl", "list-sessions"],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)
	process_loginctl_list_sessions.wait()
	for line_loginctl_list_sessions in process_loginctl_list_sessions.stdout:
		if do_log % log_frequency == 0: print(f"{line_loginctl_list_sessions}", flush=True)
		if "user" in line_loginctl_list_sessions:
			session_number = line_loginctl_list_sessions.split()[0]
	return session_number

# See if the screen is locked.
def is_screen_locked(session_number, do_log):
	screen_is_locked = True
	process_loginctl_show_session = subprocess.Popen(
		["loginctl", "show-session", session_number, "--property=LockedHint"],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)
	process_loginctl_show_session.wait()
	for line_loginctl_show_session in process_loginctl_show_session.stdout:
		if do_log % log_frequency == 0: print(f"{line_loginctl_show_session}", flush=True)
		if "LockedHint" in line_loginctl_show_session:
			if "no" in line_loginctl_show_session:
				screen_is_locked = False
	return screen_is_locked

# Start the screen saver.
def start_screensaver(do_log):
	subprocess.run(["/usr/bin/xscreensaver-command", "--activate"])

def main():
	print("Starting up XScreenSaver Wayland idle detection script.", flush=True)

	do_log = 0

	while True:
		do_log += 1
		idle_monitor_time = idle_time(do_log)
		if idle_monitor_time >= idle_blank_time:
			if do_log % log_frequency == 0: print("Too long. Checking for inhibitors.", flush=True)
			idle_is_inhibited = is_idle_inhibited(do_log)
			if not idle_is_inhibited:
				if do_log % log_frequency == 0: print("Not inhibited. Checking for screen saver running.", flush=True)
				screensaver_is_running = is_screensaver_running(do_log)
				if not screensaver_is_running:
					session_number = get_session_number(do_log)
					screen_is_locked = is_screen_locked(session_number, do_log)
					if not screen_is_locked:
						print(f"Idle time is {idle_monitor_time} ms. Screensaver is not running. Screen is not locked. Activating screensaver.", flush=True)
						start_screensaver(do_log)	
					else:
						if do_log % log_frequency == 0: print("Screen is locked. Not activating screensaver.", flush=True)
				else:
					if do_log % log_frequency == 0: print("Screen is blanked. Not activating screensaver.", flush=True)
		time.sleep(1)

if __name__=="__main__":
	main()
