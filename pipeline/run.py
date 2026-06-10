import argparse
from scrape import scrape_all
from transform import transform
from load import load_all


def main():
    parser = argparse.ArgumentParser(description='15-0.cl data pipeline')
    parser.add_argument('--scrape',    action='store_true')
    parser.add_argument('--transform', action='store_true')
    parser.add_argument('--load',      action='store_true')
    args = parser.parse_args()

    run_all = not any([args.scrape, args.transform, args.load])

    if run_all or args.scrape:
        print('=== SCRAPE ===')
        scrape_all()

    if run_all or args.transform:
        print('=== TRANSFORM ===')
        transform()

    if run_all or args.load:
        print('=== LOAD ===')
        load_all()


if __name__ == '__main__':
    main()
