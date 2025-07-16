#!/bin/env python3

lock_screen_after_seconds = 60

import subprocess, re, sys, psutil, time, datetime
import dateutil.parser

# Wait for XScreenSaver service.
def wait_xscreensaver_systemd():
	while True:
		if any(proc.info['name'] == "xscreensaver-systemd" for proc in psutil.process_iter(['name'])):
			break
		time.sleep(1)
		print("Still waiting for process xscreensaver-systemd to start...", flush=True)

# Continuously watch for screen saver activity messages.
def start_watch_command():
	return subprocess.Popen(
		["/usr/bin/xscreensaver-command", "--watch"],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)

# Lock the screen.
def lock_screen():
	subprocess.run(["/usr/bin/xdg-screensaver", "lock"])

# Process each line of output from the command.
def watch_all_output(process):
	for line in process.stdout:
		line = line.strip()
		print(f"Processing line: {line}", flush=True)
		if re.match(r"^BLANK", line):
			blank_time_string = re.search(r"^BLANK (.*)$", line).group(1)
			blank_time = dateutil.parser.parse(blank_time_string)
		if re.match(r"^UNBLANK", line):
			unblank_time_string = re.search(r"^UNBLANK (.*)$", line).group(1)
			unblank_time = dateutil.parser.parse(unblank_time_string)
			time_since_blank = unblank_time - blank_time
			if time_since_blank > datetime.timedelta(seconds=lock_screen_after_seconds):
				print(f"{int(time_since_blank.total_seconds())} seconds have passed since screensaver activated and now it's unblanking. Locking the screen...", flush=True)
				# The screen saver just stopped running and it was running for long enough. Lock the screen.
				lock_screen()
			else:
				print(f"Only {int(time_since_blank.total_seconds())} seconds have passed since screensaver activated and now it's unblanking. Not locking the screen.", flush=True)

def main():
	print("Starting up XScreenSaver Wayland lock script.", flush=True)
	
	print(f"Waiting for process xscreensaver-systemd to start...", flush=True)
	wait_xscreensaver_systemd()

	print("Process xscreensaver-systemd is running. Starting XScreenSaver command watch.", flush=True)
	process = start_watch_command()

	print("XScreenSaver command watch started, waiting for output...", flush=True)
	watch_all_output(process)

	print("XScreenSaver command watch output has ended.", flush=True)
	process.wait()
	print("XScreenSaver command watch process has exited. Ending script.", flush=True)
	sys.stdout.flush()

if __name__=="__main__":
	main()
