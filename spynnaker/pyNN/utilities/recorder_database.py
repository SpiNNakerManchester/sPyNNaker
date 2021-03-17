# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
from enum import Enum
import numpy
import os
import sqlite3
from spinn_utilities.helpful_functions import is_singleton


class TABLE_TYPES(Enum):
    EVENT = 0
    SINGLE = 1
    MATRIX = 2


_DDL_FILE = os.path.join(os.path.dirname(__file__),
                         "recorder.sql")
DEFAULT_NAME = "recorder.sqlite3"
_MAX_COLUMNS = 1990  # test as 1999 but with safety


class RecorderDatabase(object):
    """ Specific implementation of the Database for SQLite 3.

    .. note::
        NOT THREAD SAFE ON THE SAME DB.
        Threads can access different DBs just fine.

    .. note::
        This totally relies on the way SQLite's type affinities function.
        You can't port to a different database engine without a lot of work.
    """

    __slots__ = [
        # the database holding the data to store
        "_db",
    ]

    META_TABLES = ["metadata", "local_matrix_metadata", "segment_info"]

    def __init__(self, database_file=None):
        """
        :param str database_file: The name of a file that contains (or will\
            contain) an SQLite database holding the data. If omitted, an\
            unshared in-memory database will be used.
        :type database_file: str
        """
        self._db = None
        if database_file is None:
            database_file = ":memory:"  # Magic name!
        elif os.listdir(database_file):
            database_file = os.path.join(database_file, DEFAULT_NAME)
        self._db = sqlite3.connect(database_file)
        self.__init_db()

    def __del__(self):
        self.close()

    def __enter__(self):
        """ Start method is use in a ``with`` statement
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ End method if used in a ``with`` statement.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()

    def close(self):
        """ Finalises and closes the database.
        """
        if self._db is not None:
            self._db.close()
            self._db = None

    def __init_db(self):
        """ Set up the database if required.
        """
        self._db.row_factory = sqlite3.Row
        with open(_DDL_FILE) as f:
            sql = f.read()
        self._db.executescript(sql)

    def clear_ds(self):
        """ Clear all saved data
        """
        with self._db:
            names = [row["name"] for row in self._db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")]
            for name in self.META_TABLES:
                names.remove(name)
            for name in names:
                self._db.execute("DROP TABLE " + name)
            names = [row["name"] for row in self._db.execute(
                "SELECT name FROM sqlite_master WHERE type='view'")]
            for name in names:
                self._db.execute("DROP VIEW " + name)
            for name in self.META_TABLES:
                self._db.execute("DELETE FROM " + name)

    def _table_name(self, source, variable, segment):
        """
        Get a table name based on source and variable names

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :rtype: str
        """
        name = source + "_" + variable
        if segment > 0:
            name = "s{}_".format(segment) + name
        return name

    def get_variable_map(self, segment=-1):
        """
        Gets a map of sources to a list of variables:table_type

        :rtype: dict(list(str))
        """
        with self._db:
            variables = defaultdict(list)
            for row in self._db.execute(
                    """
                    SELECT source, variable, table_type
                    FROM metadata
                    WHERE segment = ?
                    GROUP BY source, variable, table_type
                    """):
                variables[row["source"]].append("{}:{}".format(
                    row["variable"], row["table_type"]))
            return variables

    def _check_table_exist(self, table_name):
        """
        Support function to see if a table already exists

        :param str table_name: name of a Table
        :return: True if and l=only if the table exists
        :type: bool
        """
        for _ in self._db.execute(
                """
                SELECT name FROM sqlite_master WHERE type='table' AND name=?
                LIMIT 1
                """, [table_name]):
            return True
        return False

    def x_get_or_create_data_table(
            self, source, variable, segment, sampling_interval, table_type):
        """
        Finds or if allowed creates a data table based on source and variable

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param table_type: Type of table to find or create
        :type table_type: TABLE_TYPES or None
        :param bool create_table:
        :return:
            The name and type of the Table.
            Name could be None if the data is too complex to get from a
            single table.
        type: (str, TABLE_TYPES) or (None, TABLE_TYPES)
        :raises:
            An Exception if an existing Table does not have the exected type
            An Expcetion if the table does not exists an create_table is False
        """
        data_table, _ = self._find_data_table(
            source, variable, segment, table_type)

        if data_table:
            return data_table

        if table_type == TABLE_TYPES.MATRIX:
            data_table = None  # data_table done later if at all
        elif table_type == TABLE_TYPES.SINGLE:
            data_table = self._create_single_table(source, variable, segment)
        elif table_type == TABLE_TYPES.EVENT:
            data_table = self._create_event_table(source, variable, segment)
        else:
            raise NotImplementedError(
                "No create table for datatype {}".format(table_type))

        self._db.execute(
            """
            INSERT OR IGNORE INTO metadata(
                source, variable, segment, data_table, table_type, n_ids,
                sampling_interval)
            VALUES(?,?,?,?,?,0,?)
            """,
            (source, variable, segment, data_table, table_type.value,
             sampling_interval))

        return data_table

    def register_data_source(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, table_type, segment=-1):
        with self._db:
            segment = self._clean_segment(segment)
            for row in self._db.execute(
                    """
                    SELECT sampling_interval, description, unit, n_neurons,
                           table_type
                    FROM metadata
                    WHERE source = ? AND variable = ? and segment = ?
                    LIMIT 1
                    """, (source, variable, segment)):
                assert (sampling_interval == row["sampling_interva"])
                assert (description == row["description"])
                assert (unit == row["unit"])
                assert (n_neurons == row["n_neurons"])
                assert (table_type.value == row["table_type"])
                return

            if table_type == TABLE_TYPES.MATRIX:
                data_table = None  # data_table done later if at all
            elif table_type == TABLE_TYPES.SINGLE:
                data_table = self._create_single_table(
                    source, variable, segment)
            elif table_type == TABLE_TYPES.EVENT:
                data_table = self._create_event_table(
                    source, variable, segment)
            else:
                raise NotImplementedError(
                    "No create table for datatype {}".format(table_type))

            self._db.execute(
                """
                INSERT INTO metadata(
                    source, variable,  segment, sampling_interval,description,
                    unit, n_neurons,  data_table, table_type, n_ids)
                VALUES(?,?,?,?,?,?,?,?,?,0)
                """,
                (source, variable, segment, sampling_interval, description,
                    unit, n_neurons, data_table, table_type.value))

    def register_event_source(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, segment=-1):
        self.register_data_source(
            source, variable, sampling_interval, description, unit,
            n_neurons, TABLE_TYPES.EVENT, segment)

    def register_matrix_source(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, segment=-1):
        self.register_data_source(
            source, variable, sampling_interval, description, unit,
            n_neurons, TABLE_TYPES.MATRIX, segment)

    def register_single_source(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, segment=-1):
        self.register_data_source(
            source, variable, sampling_interval, description, unit,
            n_neurons, TABLE_TYPES.SINGLE, segment)

    def _get_data_table(
            self, source, variable, segment, table_type):
        """
        Finds or if allowed creates a data table based on source and variable

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param table_type: Type of table to find or create
        :type table_type: TABLE_TYPES or None
        :return:
            The name and type of the Table.
            Name could be None if the data is too complex to get from a
            single table.
        type: (str, TABLE_TYPES) or (None, TABLE_TYPES)
        :raises:
            An Exception if an existing Table does not have the exected type
            An Expcetion if the table does not exists an create_table is False
        """
        data_table, table_type = self._find_data_table(
            source, variable, segment, table_type)

        # data_table may be None if data too big
        if table_type is None:
            raise Exception("No Data for {}:{}:{}".format(
                source, variable, segment))

        return data_table, table_type

    def _find_data_table(
            self, source, variable, segment, table_type):
        """
        Finds or if allowed creates a data table based on source and variable

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param table_type: Type of table to find or create
        :type table_type: TABLE_TYPES or None
        :param bool create_table:
        :return:
            The name and type of the Table.
            Name could be None if the data is too complex to get from a
            single table.
        type: (str, TABLE_TYPES) or (None, TABLE_TYPES)
        :raises:
            An Exception if an existing Table does not have the exected type
            An Expcetion if the table does not exists an create_table is False
        """
        for row in self._db.execute(
                """
                SELECT data_table, table_type
                FROM metadata
                WHERE source = ? AND variable = ? and segment = ?
                LIMIT 1
                """, (source, variable, segment)):
            if table_type:
                assert(table_type.value == row["table_type"])
            return row["data_table"], row["table_type"]
        return None, None

    def x_tables_and_views__by_segment(self, segment):
        tables = set()
        views = set()
        for row in self._db.execute(
                """
                SELECT raw_table, full_view, index_table
                FROM local_matrix_metadata
                WHERE segment = ?
                """, (segment, )):
            tables.add(row["data_table"])
            views.add(row["full_view"])
            tables.add(row["index_table"])
        for row in self._db.execute(
                """
                SELECT data_table
                FROM metadata
                WHERE segment = ?
                """, (segment, )):
            table = row["data_table"]
            if table not in views:
                tables.add(table)

        return tables, views

    def _tables_by_segment(self, segment):
        tables = set()
        views = set()
        for row in self._db.execute(
                """
                SELECT raw_table, full_view, index_table
                FROM local_matrix_metadata
                WHERE segment = ?
                """, (segment, )):
            tables.add(row["data_table"])
            views.add(row["full_view"])
        for row in self._db.execute(
                """
                SELECT data_table
                FROM metadata
                WHERE segment = ?
                """, (segment, )):
            table = row["data_table"]
            if table not in views:
                tables.add(table)

        return tables

    def _get_table_ids(self, table_name):
        """
        Gets the ids for this table

        The assumption is that names of all but the first column are ids
        in a form that can be cast to int

        :param str table_name: Name of the table to check
        :rype: list(int)
        """
        cursor = self._db.cursor()
        # Get the column names
        cursor.execute("SELECT * FROM {} LIMIT 1".format(table_name))
        ids = [int(description[0]) for description in cursor.description[1:]]
        return ids

    def _get_column_data(self, table_name):
        """
        Gets the data from single column based database.

        The assumption is that names of all but the first column are ids
        in a form that can be cast to int

        :param str table_name: Name of the table to get data for
        :return: Three numpy arrays
            - The ids of the data
            - The timestamps of the data
            - The data with shape len(timestamp), len(ids)
        :rtype: (numpy.ndarray, numpy.ndarray, numpy.ndarray)
        """
        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM {}".format(table_name))
        names = [description[0] for description in cursor.description]
        ids = numpy.array(names[1:], dtype=numpy.integer)
        values = numpy.array(cursor.fetchall())
        return ids, values[:, 0], values[:, 1:]

    def get_data(self, source, variable, segment=-1):
        """
        Gets the data for this source and variable name

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :return: One or Three numpy arrays
            - The ids of the data (Not for event/spike data)
            - The timestamps of the data  (Not for event/spike data)
            - The data with shape len(timestamp), len(ids)
            or shape (2, X) id, timestamp
        :rtype: (numpy.ndarray, numpy.ndarray, numpy.ndarray) or numpy.ndarray
        """
        with self._db:
            data_table, table_type = self._get_data_table(
                source, variable, segment, None)
            if table_type == TABLE_TYPES.MATRIX:
                return self._get_matrix_data(
                    source, variable, segment, table_type)
            if table_type == TABLE_TYPES.SINGLE:
                return self._get_column_data(data_table)
            if table_type == TABLE_TYPES.EVENT:
                return self._get_events_data(data_table)

    def _clean_data(self, timestamps, data, ids=None):
        """
        Does any cleaning of the input timestamps and data to the expected
        format.

        numpy arrays and iterables are converted to lists

        If timestamps is empty the first column of data is used as the
        timestamps

        It timestamps is not empty they are added as the first column of the
        data.

        The timestamps are converted to a list of list as that is what
        sqllite expects

        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param data: the input data
        :return: The data as lists that can be used in queries
        """
        if isinstance(timestamps, numpy.ndarray):
            if len(timestamps.shape) == 1:
                timestamps.reshape(timestamps.shape[0], 1)
                timestamps = timestamps[:, None]
        if isinstance(timestamps, (int, float)):
            sampling_interval = timestamps
            timestamps = [x * timestamps for x in range(len(data))]
        else:
            sampling_interval = None
        if isinstance(data, numpy.ndarray):
            if len(data.shape) == 1:
                data.reshape(data.shape[0], 1)
                data = data[:, None]
            if isinstance(timestamps, numpy.ndarray):
                data = numpy.hstack((timestamps, data))
                if len(timestamps) > 1:
                    sampling_interval = timestamps[1][0] - timestamps[0][0]
                else:
                    sampling_interval = 0
                return timestamps.tolist(), data.tolist(), sampling_interval
            data = data.tolist()
        else:
            data = list(data)
        if timestamps is not None and len(timestamps) > 0:
            if isinstance(timestamps, numpy.ndarray):
                timestamps = timestamps.tolist()
            elif is_singleton(timestamps[0]):
                timestamps = list(map(lambda x: [x], timestamps))
            if is_singleton(data[0]):
                data = list(map(lambda x: [x], data))
            if ids:
                assert(len(data[0]) == len(ids))
            else:
                assert (len(data[0]) == 1)
            data = list(map(lambda x, y: x + y, timestamps, data))
        else:
            if len(data) > 0:
                if ids:
                    assert(len(data[0]) == len(ids) + 1)
                else:
                    assert (len(data[0]) == 2)
            timestamps = [[row[0]] for row in data]
        if sampling_interval is None:
            if len(timestamps) > 1:
                sampling_interval = timestamps[1][0] - timestamps[0][0]
            else:
                sampling_interval = 0
        return timestamps, data, sampling_interval

    def _split_data(self, data, ids):
        cutoff = 0
        while cutoff < len(data[0]):
            data_block = list(
                map(lambda x:
                    x[0:1] + x[cutoff + 1:cutoff + _MAX_COLUMNS + 1], data))
            ids_block = ids[cutoff:cutoff + _MAX_COLUMNS]
            yield data_block, ids_block
            cutoff += _MAX_COLUMNS

    def _clean_segment(self, segment):
        """
        Does any cleaning for the segemnt.

        For example converting minus numbers by counting from max

        :param int segment: Number of the segment / reset group
        :return: a clean/ adjusted segment
        :type: int
        """
        if segment < 0:
            current = self.current_segment()
            use_segment = segment + current + 1
        else:
            use_segment = segment

        segments = self.get_segments()
        if use_segment in segments:
            return use_segment
        raise Exception(
            "Segment {} not found. Known segments are {}"
            "".format(segment, segments.keys))

    # matrix data

    def insert_matrix(self, source, variable, data, ids=None, timestamps=None,
                      sampling_interval=None, segment=-1):
        """
        Inserts matrix data into the database

        This method can be called multiple times with the same source and
        variable, and multiple distinct ids lists. The assumption is that no
        id will be in more than one of these distinct lists,
        and that the lists will be in the same order each time.

        The data will be a 2D array where the first column is the timestamp
        and the one column for each id.

        There can ever only be a single value per timestamp, id pair.

        The get methods deal with missing data so there is not requirement
        that every timestamp has data for all ids lists.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: 2d array of shape (X, len(ids)+1)
        :type data: iterable(iterable(int) or numpty.ndarray
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param iterable(int) ids: The ids for the data.
        :param int segment: Number of the segment / reset group
       """
        if len(data) == 0:
            return
        timestamps, data, sampling_interval = self._clean_data(
            timestamps, data, ids)
        segment = self._clean_segment(segment)
        with self._db:
            if len(data[0]) < _MAX_COLUMNS:
                self._insert_matrix(source, variable, data, ids, timestamps,
                                    segment, sampling_interval)
            else:
                for data_block, ids_block in self._split_data(data, ids):
                    self._insert_matrix(
                        source, variable, data_block, ids_block, timestamps,
                        segment, sampling_interval)

    def _insert_matrix(
            self, source, variable, data, ids, timestamps, segment,
            sampling_interval):
        """
        Inserts matrix data into the database

        This method can be called multiple times with the same source and
        variable, and multiple distinct ids lists. The assumption is that no
        id will be in more than one of these distinct lists,
        and that the lists will be in the same order each time.

        The data will be a 2D array where the first column is the timestamp
        and the one column for each id.

        There can ever only be a single value per timestamp, id pair.

        The get methods deal with missing data so there is not requirement
        that every timestamp has data for all ids lists.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: 2d array of shape (X, len(ids)+1)
        :type data: iterable(iterable(int) or numpty.ndarray
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param iterable(int) ids: The ids for the data.
        :param int segment: Number of the segment / reset group
       """
        raw_table, index_table = self._get_matrix_raw_table(
            source, variable, segment, sampling_interval, ids)

        cursor = self._db.cursor()
        # Get the number of columns
        cursor.execute("SELECT * FROM {} LIMIT 1".format(raw_table))
        query = "INSERT INTO {} VALUES ({})".format(
            raw_table, ",".join("?" for _ in cursor.description))
        print(query)
        cursor.executemany(query, data)

        query = "INSERT OR IGNORE INTO {} VALUES(?)".format(index_table)
        self._db.executemany(query, timestamps)

    def _get_matrix_raw_table(
            self, source, variable, segment, sampling_interval, ids):
        """
        Get or create a raw table to store local/core matrix data in

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param interable(ids) ids: Ids for this ocal/core
        :return: name of raw data table
        :rtype: str
        """
        for row in self._db.execute(
                """
                SELECT raw_table, index_table
                FROM local_matrix_metadata
                WHERE source = ? AND variable = ? AND segment = ?
                    AND first_id = ?
                LIMIT 1
                """, (source, variable, segment, ids[0])):
            table_name = row["raw_table"]
            index_table = row["index_table"]
            check_ids = self._get_table_ids(table_name)
            assert(check_ids == list(ids))
            return (table_name, index_table)

        return self._create_matrix_raw_table(
            source, variable, segment, sampling_interval, ids)

    def _create_matrix_raw_table(
            self,  source, variable, segment, sampling_interval, ids):
        """
        Creates the raw table to store local/core matrix data in

        Also creates a view to include any missing timestamps
        and registers both with the local_matrix_metadata database

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param interable(ids) ids: Ids for this ocal/core
        :return: name of raw data table
        :param int segment: Number of the segment / reset group
        :rtype: str
        """
        full_view = (self._table_name(source, variable, segment)
                     + "_" + str(ids[0]))
        raw_table = full_view + "_raw"

        # Create the raw table
        timestamp = "timestamp FLOAT NOT NULL"
        ids_str = ",".join(["'" + str(id) + "' INTEGER" for id in ids])
        ddl_statement = "CREATE TABLE IF NOT EXISTS {} ({}, {})".format(
            raw_table, timestamp, ids_str)
        self._db.execute(ddl_statement)

        index_table = self._get_matix_index_table(source, variable, segment)

        # create full view
        ddl_statement = """
            CREATE VIEW {}
            AS SELECT * FROM {} LEFT JOIN {} USING (timestamp)
            """
        ddl_statement = ddl_statement.format(full_view, index_table, raw_table)
        self._db.execute(ddl_statement)

        self._db.execute(
            """
            INSERT OR IGNORE INTO local_matrix_metadata(
                source, variable, segment, raw_table, full_view, index_table,
                first_id)
            VALUES(?,?,?,?,?,?, ?)
            """,
            (source, variable, segment, raw_table, full_view, index_table,
             ids[0]))

        self._update_global_matrix_view(
            source, variable, segment, raw_table, len(ids))

        return raw_table, index_table

    def _get_matix_index_table(self, source, variable, segment):
        """
        Get and if needed creates an index table for the timestamps.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :return: name of the index table
        :param int segment: Number of the segment / reset group
        :rtype: str
        """
        index_table = self._table_name(source, variable, segment) + "_indexes"
        ddl_statement = """
            CREATE TABLE IF NOT EXISTS {}
            (timestamp FLOAT PRIMARY KEY ASC)
            """.format(index_table)
        self._db.execute(ddl_statement)

        return index_table

    def _update_global_matrix_view(
            self, source, variable, segment, raw_table, n_ids):
        """
        Updates the metddata data_table and n_neurons  for this data

        If there is only one local table for this data the data_table is
        the raw_table

        If there is more than one local table and it is possible a view is
        created combining all the local full views.

        If there are too many ids/columns to handle in a view data_table
        is set to None to indicating that the local data must be contatenated.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param str raw_table: Name of the raw table just created
        :param n_ids: Number of ids of the local tables just added
        """
        self._db.execute(
            """
            UPDATE metadata
            SET n_ids = n_ids + ?
            WHERE source = ? and variable = ? and segment = ?
            """,
            (n_ids, source, variable, segment))

        for row in self._db.execute(
                """
                SELECT n_ids FROM metadata
                WHERE source = ? AND variable = ? and segment = ?
                LIMIT 1
                """, (source, variable, segment)):
            new_n_ids = row["n_ids"]

        if new_n_ids == n_ids:
            global_view = raw_table
        else:
            global_view = self._table_name(source, variable, segment) + "_all"
            ddl_statement = "DROP VIEW IF EXISTS {}".format(global_view)
            self._db.execute(ddl_statement)
            if new_n_ids < _MAX_COLUMNS:
                local_views = self._get_local_views(source, variable)
                ddl_statement = "CREATE VIEW {} AS SELECT * FROM {}".format(
                    global_view, " NATURAL JOIN ".join(local_views))
                print(ddl_statement)
                self._db.execute(ddl_statement)
            else:
                global_view = None

        self._db.execute(
            """
            UPDATE metadata
            SET data_table = ?
            WHERE source = ? and variable = ?
            """,
            (global_view, source, variable))

    def _get_local_views(self, source, variable, segment):
        """
        Gets a list of all the local views for this source and variable

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :rtype: list(str)
        """
        local_views = []
        for row in self._db.execute(
                """
                SELECT full_view
                FROM local_matrix_metadata
                WHERE source = ? AND variable = ? and segment = ?
                ORDER BY first_id
                """, (source, variable, segment)):
            local_views.append(row["full_view"])
        return local_views

    def get_matrix_data(self, source, variable, segment=-1):
        """
        Retreives the matrix data for this source and variable.

        If a single view is avaiable that is used,
        otherwise the local data is concatenated.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :raises: An expception if there is not data for this source and
            variable, or if it is nt matrix data
        :return: Three numpy arrays
            - The ids of the data
            - The timestamps of the data
            - The data with shape len(timestamp), len(ids)
        :rtype: (numpy.ndarray, numpy.ndarray, numpy.ndarray)
        """
        segment = self._clean_segment(segment)
        with self._db:
            data_table, _ = self._get_data_table(
                source, variable, segment, TABLE_TYPES.MATRIX)
            return self._get_matrix_data(
                source, variable, segment, data_table)

    def _get_matrix_data(self, source, variable, segment, data_table):
        """
        Retreives the matrix data for this source and variable.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param data_table: Name of the single view to use or None if the
            local data must be concatenated
        :type data_table: str or None
        :return: Three numpy arrays
            - The ids of the data
            - The timestamps of the data
            - The data with shape len(timestamp), len(ids)
        :rtype: (numpy.ndarray, numpy.ndarray, numpy.ndarray)
        """
        if data_table:
            return self._get_column_data(data_table)

        local_views = self._get_local_views(source, variable, segment)
        all_ids = []
        all_local_data = []
        for local_view in local_views:
            local_ids, timestamps, local_data = self._get_column_data(
                local_view)
            all_ids.append(local_ids)
            all_local_data.append(local_data)
        ids = numpy.hstack(all_ids)
        data = numpy.hstack(all_local_data)
        return ids, timestamps, data

    # Events data

    def insert_events(
            self, source, variable, data, timestamps=None, segment=-1):
        """
        Inserts events/ spikes data

        There can be more than one evet/spike for a timestamp, id pair

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: Data to store in the format timestamp, id or just id
        :type data: iterable((int, int) oriterable(int) or  numpy.ndarray
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param int segment: Number of the segment / reset group
        """
        _, data, sampling_interval = self._clean_data(timestamps, data)
        segment = self._clean_segment(segment)
        with self._db:
            data_table, _ = self._get_data_table(
                source, variable, segment, TABLE_TYPES.EVENT)
            query = "INSERT INTO {} VALUES (?, ?)".format(data_table)
            print(query)
            self._db.executemany(query, data)

    def _create_event_table(self, source, variable, segment):
        """
        Creates a table to hold events data

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :return: Name of the events table
        :param int segment: Number of the segment / reset group
        :rtype: str
        """
        data_table = self._table_name(source, variable, segment)
        ddl_statement = """
            CREATE TABLE IF NOT EXISTS {} (
            timestamp FLOAT NOT NULL,
            id INTEGER NOT NULL)
            """.format(data_table)
        self._db.execute(ddl_statement)
        return data_table

    def get_events_data(self, source, variable, segment=-1):
        """
        Gets the events/spikes data for this source and variable

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :return: The events data in the shape (x, 2) where the columns are
            timestamp, id
        :rtype: numpy.ndarray
        """
        segment = self._clean_segment(segment)
        with self._db:
            data_table, _ = self._get_data_table(
                source, variable, segment, TABLE_TYPES.EVENT)
            return self._get_events_data(data_table)

    def _get_events_data(self, data_table):
        """
        Gets the events/spikes data from this table

        :param str data_table: name of table to get data from
        :return: The events data in the shape (x, 2) where the columns are
            timestamp, id
        :rtype: numpy.ndarray
        """
        cursor = self._db.cursor()
        cursor.execute("SELECT timestamp, id FROM {}".format(data_table))
        return numpy.array(cursor.fetchall())

    # single data

    def insert_single(self, source, variable, data, id, timestamps=None,
                      segment=-1):
        """
        Inserts data where there is only a single column of local data for
        each core

        Will add columns to the table as need.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: Data in the shape (x, 2) where the columns are
        timestamp, value
        :type data: iterable((int, int)) or numpy.ndarray
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param int id:
        :param int segment: Number of the segment / reset group
        """
        timestamps, data, sampling_interval = self._clean_data(
            timestamps, data)
        segment = self._clean_segment(segment)
        with self._db:
            data_table, _ = self._get_data_table(
                source, variable, segment, TABLE_TYPES.SINGLE)

            # Make sure a column exists for this id
            # Different cores will have different ids so no safetly needed
            ids_in_table = self._get_table_ids(data_table)
            if id not in ids_in_table:
                ddl = "ALTER TABLE {} ADD '{}' INTEGER".format(data_table, id)
                print(ddl)
                self._db.execute(ddl)

            # make sure rows exist for each timestamp
            query = "INSERT or IGNORE INTO {}(timestamp) VALUES (?)"
            query = query.format(data_table)
            print(query)
            timestamps = [[row[0]] for row in data]
            self._db.executemany(query, timestamps)

            # update the rows with the data
            query = "UPDATE {} SET '{}' = ? where timestamp = ?"
            query = query.format(data_table, id)
            print(query)
            values = [[row[1], row[0]] for row in data]
            self._db.executemany(query, values)

    def _create_single_table(self, source, variable, segment):
        """
        Creates a table to hold the single column data as it arrives.

        The table starts of with only a timestamp column with additional id
        columns added on the fly as needed.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :return:
        """
        data_table = self._table_name(source, variable, segment)
        ddl_statement = """
            CREATE TABLE  IF NOT EXISTS {} (
            timestamp FLOAT NOTE NONE)
            """.format(data_table)
        self._db.execute(ddl_statement)
        return data_table

    def get_single_data(self, source, variable, segment=-1):
        """
        Gets all the data (entered as single columns) for this source and
        variable

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :return: Three numpy arrays
            - The ids of the data
            - The timestamps of the data
            - The data with shape len(timestamp), len(ids)
        :rtype: (numpy.ndarray, numpy.ndarray, numpy.ndarray)
        """
        segment = self._clean_segment(segment)
        with self._db:
            data_table, _ = self._get_data_table(
                source, variable, segment, TABLE_TYPES.SINGLE)
            return self._get_column_data(data_table)

    def update_segment(self, segment, start_timestamp, end_timestamp):
        with self._db:
            if self._db.execute(
                    """
                    INSERT OR IGNORE INTO segment_info(
                        segment, start_timestamp, end_timestamp)
                    VALUES(?,?,?)
                    """, (segment, start_timestamp, end_timestamp)).rowcount == 1:
                return
            for row in self._db.execute(
                    "SELECT * FROM segment_info WHERE segment = ?",
                    (segment, )):
                assert start_timestamp == row["start_timestamp"]
                if end_timestamp > row["end_timestamp"]:
                    self._db.execute(
                        """
                            UPDATE segment_info	
                            SET end_timestamp = ?
                            WHERE segment = ?
                        """, (end_timestamp, segment))
                    self._clear_segment(segment)
                elif end_timestamp < row["end_timestamp"]:
                    raise Exception(
                        "Segment {} was already has an end_timestamp of {} "
                        "so new value of {} does not make sense".format(
                            segment, row["end_timestamp"], end_timestamp))

    def _clear_segment(self, segment):
        tables = self._tables_by_segment(segment)
        for table in tables:
            self._db.execute("DELETE FROM {}".format(table))

    def get_segments(self):
        with self._db:
            segments = dict()
            for row in self._db.execute("SELECT * FROM segment_info"):
                segments[row["segment"]] = (
                    row["start_timestamp"], row["end_timestamp"])
        return segments

    def get_source_segment_data(self, source, segment):
        variables = {}
        with self._db:
            for row in self._db.execute(
                    """
                    SELECT variable, sampling_interval, description, unit,
                           n_neurons, table_type, start_timestamp,
                           end_timestamp
                    FROM metadata, segment_info
                    WHERE source = ? and metadata.segment = ? and
                           segment_info.segment = ?""",
                    (source, segment, segment)):
                v_data = {}
                v_data["sampling_interval"] = row["sampling_interval"]
                v_data["description"] = row["description"]
                v_data["unit"] = row["unit"]
                v_data["n_neurons"] = row["n_neurons"]
                v_data["table_type"] = TABLE_TYPES(row["table_type"])
                v_data["start_timestamp"] = row["start_timestamp"]
                v_data["end_timestamp"] = row["end_timestamp"]
                variables[row["variable"]] = v_data
        return variables

    def current_segment(self):
        with self._db:
            for row in self._db.execute(
                    "SELECT MAX(segment) AS max FROM segment_info"):
                return row["max"]
