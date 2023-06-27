
# linux perf with chrome
If you want to use linux perf together with chrome to profile applications in the browser you need
to follow these steps:
1. Launch Chrome from the commandline with the needed V8 flags
2. Use Linux perf on the active render process of Chrome, which can be found in Chrome's task
manager (accessible by pressing 'Shift + Esc')
3. Navigate to the website you want to profile
4. Once the execution on the website is complete, close the browser
5. Combine the gathered data from Linux perf with the performance samples of V8 using `perf inject`

Make sure to run these steps in a new folder since proflining in Chrome will generate lots of files.

## Launch Chrome with the needed flags
```
	chromium \
		--user-data-dir=`mktemp -d` \
		--no-sandbox --incognito --enable-benchmarking \
		--js-flags='--perf-prof --no-write-protect-code-memory --interpreted-frames-native-stack'
```
**--user-data-dir="mktemp -d"**  
Is used to create a fresh profile, use this to avoid caches and potential side-effects from
installed extensions (optional)

**--no-sandbox**  
Turns off the renderer sandbox so chrome can write to the log file

**--incognito**  
Is used to further prevent pollution of your results (optional)

**--enable-benchmarking**  
Enables the benchmarking extensions

**--js-flags**  
We use this flag to pass flags to V8

**--perf-prof**  
Enable linux profiler in V8

**--no-write-protect-code-memory**  
This is necessary because perf discards information about code pages when it sees the event
corresponding to removing the write bit from the code page

**--interpreted-frames-native-stack**  
Is used to create different entry points for interpreted functions so they can be distinguished by
perf based on the address alone.

## Perf record with chrome
```
	perf record --call-graph=fp --freq=max --clockid=mono -p RENDER_PID
```
**--call-graph=fp**  
Enables call-graph recording, for both kernel space and user space.
Valid options are "fp" (frame pointer), "dwarf" (DWARF's CFI - Call Frame Information)
or "lbr" (Hardware Last Branch Record facility). In order to get a proper call-graph in chrome
the "fp" option is needed.

**--freq=max**  
Profile at this frequency. Use max to use the currently maximum allowed frequency.

**--clockid=mono**  
Sets the clock id to use for the various time fields in the perf_event_type record.
This is necessary since VMs like node/v8 use a mono clock unlike linux perf.

**-p**  
Record events on existing process ID, in this chase chrome's render pid. You can get through chromes
task manager.

## Post-processing with perf inject
```
	perf inject --jit --input=perf.data --output=perf.data.jitted
```
**--jit**  
Process jitdump files by injecting the mmap records corresponding to jitted functions. This option
also generates the ELF images for each jitted function found in the jitdumps files captured in the
input perf.data file. Use this option if you are monitoring environment using JIT runtimes, such
as Java, DART or V8.

**-i, --input=**  
Input file name. (default: stdin)

**-o, --output=**  
Output file name. (default: stdout)
