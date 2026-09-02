import csv
from pathlib import Path

from sqlalchemy import select, func

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


class CSVImportService:

    HEADER_MAP = {
        "reporting_mark": [
            "Reporting Mark",
            "ReportingMark",
            "Reporting",
            "Road",
        ],
        "number": [
            "Number",
            "Road Number",
            "Car Number",
        ],
        "owner": [
            "Owner",
            "Railroad",
        ],
        "car_type": [
            "Type",
            "Car Type",
        ],
        "length": [
            "Length",
            "Car Length",
            "Size",
        ],
        "empty_weight_lbs": [
            "Empty Weight (lb)",
            "Empty Weight",
            "LT WT",
        ],
        "load_limit_lbs": [
            "Load Limit (lb)",
            "Load Limit",
            "LD LMT",
        ],
        "status": [
            "Status",
        ],
        "location": [
            "Location",
            "Current Location",
        ],
    }


    @classmethod
    def _value(cls, row, field):

        for header in cls.HEADER_MAP[field]:

            if header in row:

                return (
                    row[header] or ""
                ).strip()

        return ""



    @staticmethod
    def _normalize_mark(value):

        return (
            value
            .strip()
            .upper()
        )



    @staticmethod
    def _normalize_number(value):

        return (
            value
            .strip()
        )



    @classmethod
    def import_cars(
        cls,
        filename
    ):

        filename = Path(filename)

        if not filename.exists():

            raise FileNotFoundError(filename)


        imported = 0
        skipped = 0
        duplicates = 0
        errors = []


        with SessionLocal() as session:

            with open(
                filename,
                newline="",
                encoding="utf-8-sig",
            ) as csvfile:


                reader = csv.DictReader(csvfile)


                for line_number, row in enumerate(
                    reader,
                    start=2,
                ):

                    try:

                        reporting_mark = cls._normalize_mark(
                            cls._value(
                                row,
                                "reporting_mark",
                            )
                        )

                        number = cls._normalize_number(
                            cls._value(
                                row,
                                "number",
                            )
                        )

                        owner = cls._value(
                            row,
                            "owner",
                        )

                        car_type = cls._value(
                            row,
                            "car_type",
                        )

                        status = cls._value(
                            row,
                            "status",
                        )

                        location = cls._value(
                            row,
                            "location",
                        )

                        length_text = cls._value(
                            row,
                            "length",
                        )

                        empty_weight_text = cls._value(
                            row,
                            "empty_weight_lbs",
                        )

                        load_limit_text = cls._value(
                            row,
                            "load_limit_lbs",
                        )


                        if not reporting_mark:

                            skipped += 1

                            errors.append(
                                f"Line {line_number}: Missing Reporting Mark"
                            )

                            continue


                        if not number:

                            skipped += 1

                            errors.append(
                                f"Line {line_number}: Missing Car Number"
                            )

                            continue



                        existing = session.execute(
                            select(Car)
                            .where(
                                func.upper(
                                    func.trim(
                                        Car.reporting_mark
                                    )
                                )
                                ==
                                reporting_mark,

                                func.trim(
                                    Car.number
                                )
                                ==
                                number,
                            )
                        ).scalar_one_or_none()



                        if existing:

                            existing.owner = owner
                            existing.car_type = car_type

                            if status:

                                existing.status = status

                            if location:

                                existing.location = location


                            duplicates += 1
                            skipped += 1

                            continue



                        length = None


                        if length_text:

                            try:

                                length = int(
                                    length_text
                                )

                            except ValueError:

                                skipped += 1

                                errors.append(
                                    f"Line {line_number}: Invalid Length '{length_text}'"
                                )

                                continue

                        empty_weight_lbs = None

                        if empty_weight_text:

                            try:

                                empty_weight_lbs = int(
                                    empty_weight_text.replace(",", "")
                                )

                            except ValueError:

                                skipped += 1

                                errors.append(
                                    f"Line {line_number}: Invalid Weight "
                                    f"'{empty_weight_text}'"
                                )

                                continue

                        load_limit_lbs = None

                        if load_limit_text:

                            try:

                                load_limit_lbs = int(
                                    load_limit_text.replace(",", "")
                                )

                            except ValueError:

                                skipped += 1

                                errors.append(
                                    f"Line {line_number}: Invalid Load Limit "
                                    f"'{load_limit_text}'"
                                )

                                continue



                        car = Car(
                            reporting_mark=reporting_mark,
                            number=number,
                            owner=owner,
                            car_type=car_type,
                            length=length,
                            empty_weight_lbs=empty_weight_lbs,
                            load_limit_lbs=load_limit_lbs,
                            status=status or "Empty",
                            location=location or "Unassigned",
                        )


                        session.add(car)

                        imported += 1



                    except Exception as ex:

                        skipped += 1

                        errors.append(
                            f"Line {line_number}: {ex}"
                        )



                session.commit()


        return {
            "imported": imported,
            "duplicates": duplicates,
            "skipped": skipped,
            "errors": errors,
        }
