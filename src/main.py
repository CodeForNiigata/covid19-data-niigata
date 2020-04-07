from covid19_json import main as covid19_json_main
from niigata_csv import main as niigata_csv_main
from niigata_pdf import main as niigata_pdf_main


def main():
    niigata_pdf_main()
    niigata_csv_main()
    covid19_json_main()


if __name__ == '__main__':
    main()
