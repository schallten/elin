import sys
import os

def parser(line: bytes, filename: str) -> None:
    print(f"file={filename} line={line.decode()}")

def read_lines(path: str) -> list[bytes]:
    with open(path, "rb") as f:
        return [line.rstrip(b"\n") for line in f]

def main() -> None:
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <codefile.elin>")
        return

    code_file = sys.argv[1]

    # strip extension
    stem = os.path.splitext(os.path.basename(code_file))[0]

    lines = read_lines(code_file)

    for line in lines:
        parser(line, stem)

if __name__ == "__main__":
    main()
