# general commands
`perf version --build-option`  
Shows the perf version and all build options the version has enabled

# perf record
The **perf record** command executes a specified command and collects a performance counter profile
from it. By default, the collected data is saved into perf.data. Note that the command itself does
not display any output.

`perf record <command>`  
Record a command and save its profile into perf.data (default)

`perf record <command> -o <output file name>`  
Record a command and save its profile into a custom file

`perf record -a <command>`  
Record a command with System-wide collection from all CPUs

`perf record -F 99 <command>`  
Record a command at a frequency of 99

`perf record -p <PID>`  
Record events on existing process ID

`perf record -g <command>`  
Enables call-graph (stack chain/backtrace) recording for both kernel space and user space.

`perf record -a <event> <command>`  
Record samples on a specific event for command. you can use *perf list* to list all events

# perf report
The **perf report** command displays the performance counter profile information recorded via perf
record. By default **perf report** tries to use a TUI (Text User Interface) which is very easy to
navigate. While viewing a report, you can press 'h' to access a help window with instructions on
various actions you can perform, such as symbol annotation.

`perf report`  
Display perf.data

`perf report -i <input_data>`  
Display input data, default is perf.data 

`perf report --stdio`  
Uses the stdio interface.

`perf report --header-only`  
Show only perf.data header 

`perf report --no-children`  
Don't accumulate a callchain of children if a call chain was recorded. Can be handy when perf report
was gathered with -g

# perf annotate
**perf annotate** reads perf.data file and displays an annotated version of the code. If the object
file has debug symbols then the source code will be displayed alongside assembly code. If there is
no debug information in the object, then annotated assembly is displayed.  

`perf annotate`  
Disassemble and annotate perf.data

`perf annotate -i <input_data>`  
Disassemble and annotate input data

`perf annotate --symbol=<symbol_name>`  
Will only show annotated output for symbol name and not the full perf report

`perf annotate --asm-raw`  
Show raw instruction encoding of assembly instructions.

# perf script
The **perf script** command reads the perf.data file (created by perf record) and displays the trace
output.

`perf script`  
List all events from perf.data

`perf script -i <input_file>`  
List all events from input file

`perf script --show-mmap-events`  
Display mmap related events (e.g. MMAP, MMAP2)
