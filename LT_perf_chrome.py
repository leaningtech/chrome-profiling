#!/usr/bin/env python3

import optparse
import shlex
import os
import re
import subprocess
import time
import signal
from pathlib import Path
import colorama

# ==============================================================================
# log

def log_message(msg):
	print("")
	print("-" * 60)
	print(msg)
	print("-" * 60)

colorama.init()
def log_error(msg):
	print("")
	print("-" * 60)
	print(f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} {msg}")
	print("-" * 60)
	print("")

# ==============================================================================
# parser options

usage = """
	%prog --url=URL [OPTIONS]

This script will launch Chrome with custom flags to enable profiling and get support
to resolve JS function names. It then executes linux perf on the current open tab.

The profiling data will be written to the specified --perf-dir directory. If no directory
is provided, it will be written to the current directory.

Do not open additional tabs in the chrome instance this script launches, otherwise it will
not be able to grep the right chrome render id.

For more info use the --help option or have a look at the README.md file.
"""

parser = optparse.OptionParser(usage=usage)
parser.add_option(
	'--url',
	default=None,
	help="URL to visit when chrome started.")
parser.add_option(
	'--perf',
	default=None,
	help="Path to perf source binary. Optional.")
parser.add_option(
	'--chrome',
	default=None,
	help="Path to chrome source binary. Optional.")
parser.add_option(
	'--perf-dir',
	default=None,
	help="Path to dir where the reports will be saved. If none is provided pwd is used.")
parser.add_option(
	'--freq',
	default="max",
	help="Profile at this frequency. Default --freq=max")
parser.add_option(
	'--wait',
	action="store_true", 
	help="The script will wait for user input and will not start profiling right away.")
parser.add_option(
	'--perf-options',
	default=None,
	help="Additional perf options as comma seperated list")
parser.add_option(
	'--chrome-options',
	default=None,
	help="Additional chrome options as comma seperated list")
parser.add_option(
	'--js-flags',
	default=None,
	help="Additional js flags as comma seperated list")

# ==============================================================================
# parsing

(options, args) = parser.parse_args()

if options.url is None:
	parser.error("Please provide a URL")

if options.perf:
	perf_source = Path(options.perf).absolute()
	if not perf_source.exists():
		parser.error(f"Linux perf binary '{perf_source}' does not exist")
else:
	perf_source = "perf"

if options.chrome is None:
	if "ID=ubuntu" in open("/etc/os-release").read():
		chrome_exe = "chromium-browser"
	else:
		chrome_exe = "chromium"
else:
	chrome_exe = Path(options.chrome).absolute()
	if not chrome_exe.exists():
		parser.error(f"Chrome binary '{chrome_exe}' does not exist")

if options.perf_dir:
	perf_dir_path = Path(options.perf_dir).absolute()
	perf_dir_path.mkdir(parents=True, exist_ok=True)
	if not perf_dir_path.is_dir():
		parser.error(f"--perf-dir={perf_dir_path} is not a directory or does not exist.")

# ==============================================================================
# changing the enviroment if needed

if options.perf_dir:
	original_dir = os.getcwd()
	os.chdir(perf_dir_path)

# ==============================================================================
# helper function to find the right render pid of the chrome proccess

cpu_amount = 0
def find_renderer(parent_pid):
	global cpu_amount
	ret = None
	cmd = ["ps", "h", "-o", "pid", "--ppid", str(parent_pid)]
	child_pids = subprocess.run(cmd, capture_output=True, text=True)
	for pid in child_pids.stdout.splitlines():
		type = subprocess.getoutput([f'ps -f --pid {pid}'])
		zygote = re.search('--type=zygote', type)
		if zygote:
			ret = find_renderer(int(pid))
		renderer = re.search('--type=renderer', type)
		extension = re.search('--extension-process', type)
		cpu = re.search('^(?:\D*\d+){2}\D*(\d+)', type)
		if renderer and extension is None and int(cpu.group(1)) > cpu_amount:
			cpu_amount = int(cpu.group(1))
			ret = int(pid)
	return ret

# ==============================================================================
# graceful exit

def handle_exit():
	if options.perf_dir is not None:
		os.chdir(original_dir)
	exit(1)

# ==============================================================================
# chrome cmd

js_flags_perf = ("--perf-prof", "--no-write-protect-code-memory", "--interpreted-frames-native-stack")
chrome_cmd = [
		f"{chrome_exe}",
		"--no-sandbox",
		"--incognito",
		"--enable-benchmarking",
		"--no-first-run",
		"--no-default-browser-check",
		"--ignore-certificate-errors"
	]

# adding additional chrome and js options
if options.chrome_options:
	chrome_cmd.extend(options.chrome_options.split(","))

js_flags = set(js_flags_perf)
if options.js_flags:
	js_flags.update(shlex.split(options.js_flags))

chrome_cmd += [f"--js-flags={','.join(list(js_flags))}"]

if options.url:
	chrome_cmd += shlex.split(options.url)

# ==============================================================================
# chrome and perf record subprocess

perf = None
perf_record = [f"{perf_source}", "record", f"--freq={options.freq}", "--clockid=mono", "-p"]
log_message(f"LAUNCHING CHROME")
print(f"chrome command: {shlex.join(chrome_cmd)}")

try:
	#crome subprocess
	chrome = subprocess.Popen(chrome_cmd, start_new_session=True, stderr=subprocess.DEVNULL)
	time.sleep(1)
	print(f"Chrome's main pid: {chrome.pid}")
	start_time = time.time()
	render_pid = None
	# getting chrome's render process id
	while time.time() - start_time < 1:
		render_pid = find_renderer(chrome.pid)
		if render_pid is not None:
			break
	if render_pid is None:
		log_error("Could not retrieve chrome render pid")
		handle_exit()
	print(f"Render pid found: {render_pid}")
	# wait for user input to start profiling if needed
	if options.wait:
		input("\nPress Enter to start profiling.")
	# adding pid to perf cmd and additional options if present
	perf_record += shlex.split(f"{render_pid}")
	if options.perf_options:
		perf_record.extend(options.perf_options.split(","))
	# perf subprocess
	log_message("RUNNING PERF RECORD")
	print(f"linux perf command: {shlex.join(perf_record)}")
	print(">> Press CTRL + c to stop recording or close Chrome <<\n")
	perf = subprocess.Popen(perf_record, start_new_session=True, stdin=subprocess.PIPE)
	return_code = perf.wait()
	if return_code != 0:
		log_error("Perf record failed")
		chrome.send_signal(signal.SIGINT)
		chrome.wait()
		handle_exit()
except KeyboardInterrupt:
	chrome.send_signal(signal.SIGINT)
	chrome.wait()
	if perf:
		perf.send_signal(signal.SIGINT)
		perf.wait()
	else:
		handle_exit()

# ==============================================================================
# perf inject

perf_inject = [f"{perf_source}", "inject", "--jit", "--input=perf.data","--output=perf.data.jitted"]

log_message("POST PROCESSING: Injecting JS symbols")
print(f"Perf inject cmd: {shlex.join(perf_inject)}\nThis step might take a few moments depending on the report size")

try:
	subprocess.check_call(perf_inject)
except:
	log_error("Perf inject failed")
	handle_exit()

print("Injecting success.")
print(f"Results in: {Path.cwd()}/perf.data.jitted")

# ==============================================================================
# linux-perf analysis

result = f"{Path.cwd()}/perf.data.jitted"
if options.perf is not None:
	perf_path = f" --perf={perf_source} "
else:
	perf_path = ""

log_message("ANALYSIS")
print("linux-perf cmds:")
print(f"{perf_source} report -i {result}")
print(f"{perf_source} report --no-children -i {result}")
print(f"{perf_source} annotate -i {result} --symbol=SYMBOL_NAME")
print("")

# ==============================================================================
# exit and changing enviroment if needed

if options.perf_dir is not None:
	os.chdir(original_dir)

exit(0)
