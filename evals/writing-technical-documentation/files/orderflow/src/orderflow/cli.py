"""Operator commands. Installed as `orderflow`, or run with `python3 -m orderflow.cli`."""
import argparse
import sys

from orderflow import config, store


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orderflow", description="Operate the OrderFlow queue.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("queue-depth", help="print pending and dead-letter counts")
    requeue = sub.add_parser("requeue", help="move dead-letter orders back to pending")
    requeue.add_argument("--limit", type=int, help="move at most this many orders")
    requeue.add_argument("--dry-run", action="store_true", help="print the count without moving anything")
    args = parser.parse_args(argv)

    conn = store.connect(config.database_url())
    if args.command == "queue-depth":
        print("pending=%d dead=%d" % (store.queue_depth(conn), store.dead_letter_count(conn)))
        return 0
    if args.dry_run:
        print("would requeue %d" % store.dead_letter_count(conn))
        return 0
    print("requeued %d" % store.requeue_dead(conn, args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
