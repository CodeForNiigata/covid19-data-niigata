from inspections import create_csv as create_inspections_csv
from patients import create_csv as create_patients_csv
from querents import create_csv as create_querents_csv
from scraper import get_url
from gs import convert
import sys


def main():
    args = sys.argv
    if args[1] == 'scrape':
        patients_url, querents_url, inspections_url = get_url()
        if args[2] in {'inspections', 'all'}:
            create_inspections_csv(inspections_url)
        if args[2] in {'patients', 'all'}:
            create_patients_csv(patients_url)
        if args[2] in {'querents', 'all'}:
            create_querents_csv(querents_url)
        if not args[2] in {'all', 'inspections', 'patients', 'querents'}:
            print('invalid second argument !')
    elif args[1] == 'convert':
        convert()
    else:
        print('invalid first argument !')


if __name__ == "__main__":
    main()
