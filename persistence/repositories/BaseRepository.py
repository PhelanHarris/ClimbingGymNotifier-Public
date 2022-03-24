import sqlite3
from persistence.models.BaseModel import BaseModel


class BaseRepository:
    def __init__(self, model: BaseModel):
        self.model = model

    def get_column_names_string(self):
        return ", ".join(self.model.get_column_names())

    def find_by_id(self, id):
        conn = sqlite3.connect("hivenotifier.db")

        cursor = conn.execute(
            """SELECT id, {} FROM {}
                WHERE id = ?;
            """.format(
                self.get_column_names_string(), self.model.get_table_name()
            ),
            [id],
        )
        row = cursor.fetchone()

        conn.close()

        if row is not None:
            return self.model(*row)
        return row

    def find_all(self, where_clause=""):
        conn = sqlite3.connect("hivenotifier.db")

        cursor = conn.execute(
            """
            SELECT id, {} FROM {} {}
        """.format(
                self.get_column_names_string(),
                self.model.get_table_name(),
                where_clause,
            )
        )
        objs = []
        for row in cursor:
            objs.append(self.model(*row))

        conn.close()
        return objs

    def delete(self, obj):
        self.delete_by_id(obj.id)
        return

    def delete_by_id(self, id):
        conn = sqlite3.connect("hivenotifier.db")

        conn.execute(
            """
            DELETE FROM {} WHERE id = ?
        """.format(
                self.model.get_table_name()
            ),
            [id],
        )

        conn.commit()
        conn.close()
        return

    def save(self, obj):
        conn = sqlite3.connect("hivenotifier.db")

        if obj.id is not None and obj.id != 0:
            placeholder_string = ", ".join(
                map(
                    lambda column_name: column_name + " = ?",
                    self.model.get_column_names(),
                )
            )
            update_sql = """UPDATE {}
                SET {}
                WHERE id = ?""".format(
                self.model.get_table_name(),
                placeholder_string,
            )
            values_array = list(
                map(
                    lambda column_name: getattr(obj, column_name),
                    self.model.get_column_names(),
                )
            )
            values_array.append(obj.id)

            cursor = conn.execute(update_sql, values_array)

        else:
            placeholder_string = ", ".join(
                map(lambda column_name: "?", self.model.get_column_names())
            )
            insert_sql = """INSERT INTO {} ({})
                VALUES ({})""".format(
                self.model.get_table_name(),
                self.get_column_names_string(),
                placeholder_string,
            )
            values_array = list(
                map(
                    lambda column_name: getattr(obj, column_name),
                    self.model.get_column_names(),
                )
            )

            cursor = conn.execute(insert_sql, values_array)
            obj.id = cursor.lastrowid

        conn.commit()
        conn.close()
        return obj