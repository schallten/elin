# File I/O Operations

ELIN provides basic file handling for reading and writing data to disk (PC) or flash memory (ESP). File handles are integers (fds) that reference an internal table.

## Opening and Closing

`fopen(path)` opens a file and pushes a handle. `fclose(handle)` closes it:

```elin
let int fd = fopen("data.txt");
# ... do work ...
fclose(fd);
```

## Reading and Writing

`fread(fd)` reads one line from a file into a new string handle. `fwrite(fd, s)` writes string handle `s` to the file:

```elin
let int fd = fopen("log.txt");
fwrite(fd, "system boot\n");
fclose(fd);

let int input_fd = fopen("config.txt");
let str line = fread(input_fd);
print line;
fclose(input_fd);
```

!!! info
    On ESP hardware, these operations use LittleFS. On PC, they use standard C file streams.
