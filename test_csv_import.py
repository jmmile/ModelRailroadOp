import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.services.csv_import_service import CSVImportService


def main():

    print()
    print("===================================")
    print(" Model Railroad Operations")
    print(" CSV Import Test")
    print("===================================")
    print()

    filename = input("CSV file to import: ").strip()

    if not filename:
        print("No file specified.")
        return

    try:

        result = CSVImportService.import_cars(filename)

        print()
        print("Import Complete")
        print("----------------------------")
        print(f"Imported : {result['imported']}")
        print(f"Skipped  : {result['skipped']}")
        print(f"Errors   : {len(result['errors'])}")

        if result["errors"]:

            print()
            print("Errors")
            print("----------------------------")

            for error in result["errors"]:
                print(error)

    except FileNotFoundError:

        print()
        print("File not found.")

    except Exception as ex:

        print()
        print("Unexpected error:")
        print(ex)


if __name__ == "__main__":
    main()