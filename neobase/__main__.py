#!/usr/bin/python

import sys
from neobase import NeoBase, __version__


def main():
    import argparse

    parser = argparse.ArgumentParser(prog="NeoBase")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s, version {__version__}",
    )
    parser.add_argument(
        "keys",
        nargs="+",
        help="List of IATA codes",
    )
    parser.add_argument(
        "--date",
        help="Reference date to compute active airports",
    )
    parser.add_argument(
        "-f",
        "--field",
        default=None,
        help="search by a specific field instead of key",
    )
    parser.add_argument(
        "-w",
        "--word",
        action="store_true",
        help="like 'grep -w', only match whole words with --field",
    )
    parser.add_argument(
        "-v",
        "--invert-match",
        action="store_true",
        help="like 'grep -v', select non-matching with --field",
    )
    parser.add_argument(
        "-c",
        "--case-sensitive",
        action="store_true",
        help="opposite of 'grep -i', make the matching case-sensitive with --field",
    )
    parser.add_argument(
        "-r",
        "--radius",
        default=None,
        type=float,
        help="search by radius, in kms",
    )
    parser.add_argument(
        "--show",
        metavar="FIELD",
        nargs="*",
        help="when used, the output will look like a CSV containing those fields",
    )

    args = parser.parse_args()
    G = NeoBase(date=args.date)

    if args.show:
        import csv

        w = csv.writer(sys.stdout)
    else:
        print(f"{len(G)} points of reference")

    if args.keys == ["-"]:
        keys = (key.rstrip() for key in sys.stdin)
    else:
        keys = args.keys

    if args.field is not None:
        for key in keys:
            print("\n{:*^112s}".format(f"  {args.field}={key}  "))
            for p in G:
                needle = key
                haystack = str(G.get(p, args.field))
                if not args.case_sensitive:
                    needle = needle.lower()
                    haystack = haystack.lower()
                if args.word:  # --word means will look in words list, not substrings
                    haystack = haystack.split()
                if (needle in haystack) is args.invert_match:
                    continue
                if args.show:
                    w.writerow(G.get(p, f) for f in args.show)
                else:
                    page_rank = G.get(p, "page_rank")
                    print(
                        "{:<8s} {:<6s} {:<60s} {:<30s} {:>5s}".format(
                            p,
                            "".join(G.get(p, "location_type")),
                            G.get(p, "name"),
                            G.get(p, "country_name"),
                            "-" if page_rank is None else format(page_rank, ".1%"),
                        )
                    )

    elif args.radius is not None:
        for key in keys:
            print("\n{:*^116s}".format(f"  {key}(+{args.radius}km)  "))
            for dist, p in sorted(G.find_near(key, radius=args.radius)):
                if args.show:
                    w.writerow(G.get(p, f) for f in args.show)
                else:
                    print(
                        "{:<8s} {:<6s} {:<60s} {:<30s} {:7.1f}km".format(
                            p,
                            "".join(G.get(p, "location_type")),
                            G.get(p, "name"),
                            G.get(p, "country_name"),
                            dist,
                        )
                    )

    else:
        known_keys = []
        for key in keys:
            if key in G:
                known_keys.append(key)
            else:
                print(f"{key!r} not found in data.")

        for key in known_keys:
            if args.show:
                w.writerow(G.get(key, f) for f in args.show)
            else:
                print("\n{:*^55s}".format(f"  {key}  "))
                data = G.get(key)
                for name in sorted(data):
                    if not name.startswith("__") or data[name]:
                        print(f"{name:<20s}{repr(data[name])}")


if __name__ == "__main__":
    main()
