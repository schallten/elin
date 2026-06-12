# Debug Mode

The VM has a debug mode that prints every instruction as it runs — opcode, stack contents, and call depth. Launch it with the `--debug` flag:

```bash
./elin_vm --debug program.outz
```

You can also toggle tracing from inside an ELIN program with `trace`:

```elin
trace;    # Turn debug output ON
let int x = 42;
print x;
trace;    # Turn debug output OFF
```

!!! info
    This is invaluable when you're trying to understand why the VM produced a wrong result — it's like lifting the hood and watching every gear turn.
