import sys

ver_field = 12



for line in open(sys.argv[1]):
    parts = line.split(" | ")

    pp=parts[1].split("/")

    verno = pp[ver_field]

    print parts[0] + " | " + verno[1:]





