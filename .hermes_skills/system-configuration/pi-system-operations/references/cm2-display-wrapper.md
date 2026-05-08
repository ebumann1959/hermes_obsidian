# C Wrapper for CM2 DISPLAY Inheritance

## Problem
CM2 sets DISPLAY=:1 in its own environment but temp scripts call `conky -c <file>` via PATH lookup, losing the DISPLAY variable. Conky processes spawn but windows never appear.

## C Wrapper Source
```c
// /tmp/conky-wrapper.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char *argv[]) {
    setenv("DISPLAY", ":1", 1);
    execv("/usr/bin/conky.bin", argv);
    return 1;
}
```

## Install
```bash
sudo mv /usr/bin/conky /usr/bin/conky.bin
gcc /tmp/conky-wrapper.c -o /tmp/conky-wrapper
sudo mv /tmp/conky-wrapper /usr/bin/conky
```

## Critical: do NOT use exec in wrapper script
```bash
#!/bin/bash
# WRONG — comm field becomes conky.bin after exec; killall conky fails
exec /usr/bin/conky.bin "$@"

# CORRECT — wrapper stays alive as parent; killall conky works
#!/bin/bash
DISPLAY=:1 /usr/bin/conky.bin "$@"
```

After correct wrapper: `killall conky` works (comm=conky matches), CM2 stop works (PID-based SIGTERM), CM2 start works.
