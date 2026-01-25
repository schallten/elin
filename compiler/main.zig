const std = @import("std");

pub fn main() !void {
    const stdout = std.io.getStdOut().writer();
    const stdin = std.io.getStdIn().reader();

    try stdout.print("hello world\n", .{});

    var buffer: [256]u8 = undefined;
    const maybe_line = try stdin.readUntilDelimiterOrEof(&buffer, '\n');

    if (maybe_line) |line| {
        try stdout.print("you typed: {s}\n", .{line});
    }
}
