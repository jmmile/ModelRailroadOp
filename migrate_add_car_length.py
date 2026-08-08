from sqlalchemy import text

from modelrailroadops.database.database import engine



def migrate():

    with engine.connect() as connection:

        result = connection.execute(
            text(
                "PRAGMA table_info(cars)"
            )
        )


        columns = [
            row[1]
            for row in result.fetchall()
        ]


        if "length" in columns:

            print(
                "Column 'length' already exists."
            )

            return



        connection.execute(
            text(
                """
                ALTER TABLE cars
                ADD COLUMN length INTEGER
                """
            )
        )


        connection.commit()


        print(
            "Added 'length' column to cars table."
        )



if __name__ == "__main__":

    migrate()