from os.path import isfile
from re import findall
from sys import argv


def show_help_message():
    print("\nUsage:")
    print("./get_strings.py [FILENAME]")
    print("\n Returns a JSON blob usable in a strings file.\n")


print("\nget_strings.py\nExtract strings from python files for replacement in strings files\n\n")


# Validate args
if len(argv) != 2:
    print("Expects 2 arguments.")
    show_help_message()
    exit(1)

filename = argv[1]

if not isfile(filename):
    print(f"File {filename} does not exist.")
    show_help_message()
    exit(1)

if not filename.endswith(".py"):
    print(f"File {filename} should end with .py")
    show_help_message()
    exit(1)

# Args are now valid - on with the show
translation_regex = r"_\('([A-z0-9 ,.]+)'\)"  # _( followed by 1 or more typeable characters, followed by ')

try:
    file_handle = open(filename, "r")
except Exception:
    print(f"An error occured opening file: {filename}")
    exit(1)

file_contents = file_handle.read()

matches = findall(translation_regex, file_contents)

if matches:
    output_set = set([])
    for match in matches:
        output_set.add(match)

    print("JSON OUTPUT:\n")
    print("{")

    for match in output_set:
        fixed_match = match.replace("\n", "")
        print(f'\t"{fixed_match}": false')

    print("}")

    exit(0)

print("No strings found in file")
exit(0)
