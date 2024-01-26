
# Script usage
### Requirements
- linux-perf version 5 or higher (previous versions don't have jit support).
- Be able to run linux perf wihout sudo, you can find instructions on that further down.
### lt_perf_chrome.py
This script launches Chromium with the required terminal switches and V8 flags, and then executes
`perf record` with the render process ID of the opened Chrome tab. Once Chrome is open, you can
navigate to the desired website for profiling and then either close the browser or press Ctrl + C
in the terminal. The profiling data will be saved in the specified folder (the script creates it if
it doesn't exist), or in the current directory if no `--perf-dir=` parameter is provided.
Additionally, the script performs post-processing of the data using `perf inject`. You also have the
option to include additional V8, Chromium, and perf flags by using the parameters `--chrome-options=""`,
`--js-flags=""`, and `--perf-options=""`. 

If you haven't used linux perf before, running this script might take some time as perf will
download debug information.  

IMPORTANT: Please avoid opening additional tabs in the Chrome instance launched by this script, as
it may interfere with the correct identification of the Chrome render process ID.  

### Examples
```
./LT_perf_chrome.py --url=https://webvm.io/ --perf-dir=perf_dir
```
```
./LT_perf_chrome.py --url=https://webvm.io/ --perf=/home/builds/linux-stable/tools/perf/perf --wait
```
```
./LT_perf_chrome.py --url=https://webvm.io/ --perf-options="--call-graph=fp" --js-flags="--perf-prof-annotate-wasm"
```

# Cheatsheets
### [perf_cheatsheet.md](https://github.com/leaningtech/chrome-profiling/blob/main/perf_cheatsheet.md)
A collection of linux perf commands with examples and explanations.

### [perf_chrome_cheatsheet.md](https://github.com/leaningtech/chrome-profiling/blob/main/perf_chrome_cheatsheet.md)
If you prefer to profile Chromium without using a script, this cheatsheet provides a step-by-step
guide on how to profile Chromium using linux perf.

# Linux perf source build
A Linux perf source build is not necessary, but it can make things a little easier by ensuring that
all features of Linux perf are enabled. If you want to build Linux perf from source, you'll need to
obtain the Linux kernel source code. **This step is optional.**  
The build process itself is straightforward, and there's no need to feel overwhelmed by the kernel
source code. You won't be building an actual kernel; we only need to access the necessary tools
directory. You can get a kernel source from either of these websites:
- https://kernel.org/ 
- https://mirrors.edge.kernel.org/pub/linux/kernel/

The safest approach is to obtain a kernel version that matches your current kernel, but you can also
opt for a newer version if desired.  
Personally, I did not encounter any issues when obtaining a newer version.

## Building linux perf from source
Get the sources, either download them directly or use this command with the version you need  
```
curl -o linux-source.tar.gz https://mirrors.edge.kernel.org/pub/linux/kernel/v6.x/linux-6.0.9.tar.gz
```

Unpack the kernel source  
```
tar xvf linux-source.tar.gz
```

Move to the perf tool directory
```
cd linux-6.0.9/tools/perf
```

Build perf  
```
make
```

You may come across several build warnings, which are actually quite helpful. They indicate which
features are disabled and which packages you need to enable them. Simply install all the missing
packages and run make again.  
These are some common dependencies that may be missing:
```
sudo apt-get install libdw-dev libunwind8-dev systemtap-sdt-dev \
libaudit-dev libslang2-dev binutils-dev liblzma-dev
```

# Linux perf without sudo access
If you are using linux perf for the first time, you may encounter an error related to the 
*kernel.perf_event_paranoid* settings. To use linux perf without sudo privileges, you need to enable
certain kernel settings, which are also required for our custom script to work. Running the following
commands should enable linux perf without requiring root access.
```
sudo sh -c 'echo kernel.perf_event_paranoid=1 > /etc/sysctl.d/local.conf'
sudo sh -c 'echo kernel.kptr_restrict=0 > /etc/sysctl.d/local.conf'
```
After running these commands you should restart sysctl with this command
`sudo sysctl -p /etc/sysctl.conf` or reboot your machine.

# The build-id Cache
At the end of each run, the perf record command updates a build-id cache, with new entries for ELF
images with samples. By default, this cache is saved on disk in the $HOME/.debug directory. Over
time, this folder can become filled with data, so it's a good practice to periodically clean it out.

You can use the command `perf buildid-cache -P` to clear the cache, but I still recommend manually
reviewing and deleting the data occasionally.

# Missing symbols 
If you only see addresses in the perf report and not actually function names you might be missing
some debug symbol information. In many cases, additional debug symbol packages are available to
resolve these profiling reports. For instance, Chromium has a separate package for debug symbols,
such as "chromium-dbg" on Linux Mint. Package names may vary depending on the distribution, but they
commonly include terms like "-dbgsym" or "-dbg".

# Resources
If you want to explore the linux perf command in more depth, these resources provide in-depth
details:

- https://perf.wiki.kernel.org/index.php/Main_Page
- https://www.brendangregg.com/linuxperf.html
