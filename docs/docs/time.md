# Time & Real-Time Clock

For automation and timing, ELIN includes millisecond-precision timers and access to non-volatile RTC memory on supported hardware.

## Timing

`time()` returns milliseconds since the VM started. `delay(ms)` pauses execution:

```elin
let int start = time();
delay(1000);
let int end = time();
print end - start; # Should be approx 1000
```

## RTC Memory

`rtc_read()` and `rtc_write(val)` allow storing a single integer in the ESP's Real-Time Clock memory, which persists through deep sleep (no-op on PC):

```elin
let int boot_count = rtc_read();
boot_count = boot_count + 1;
rtc_write(boot_count);
print boot_count;
```
