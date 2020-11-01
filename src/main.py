from covid19_json import main as covid19_json_main
from niigata_csv import main as niigata_csv_main
from niigata_dl import main as niigata_dl_main


def main():
    niigata_dl_main()
    niigata_csv_main()
    covid19_json_main()


if __name__ == '__main__':
    main()
