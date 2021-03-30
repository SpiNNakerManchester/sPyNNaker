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
from spinn_front_end_common.utilities.sqlite_db import (Isolation, SQLiteDB)


class TableTypes(Enum):
    """
    Distinguish the type of table to be used
    """
    EVENT = 0
    SINGLE = 1
    MATRIX = 2


_DDL_FILE = os.path.join(os.path.dirname(__file__),  "recorder.sql")
DEFAULT_NAME = "recorder.sqlite3"

_MAX_COLUMNS = 1990  # test as 1999 but with safety


class RecorderDatabase(SQLiteDB):
    """ Specific implementation of the Database for SQLite 3.

    .. note::
        NOT THREAD SAFE ON THE SAME DB.
        Threads can access different DBs just fine.

    .. note::
        This totally relies on the way SQLite's type affinities function.
        You can't port to a different database engine without a lot of work.
    """

    __slots__ = [
        # path to the file holding the database
        "_path"
    ]

    META_TABLES = ["metadata", "local_matrix_metadata", "segment_info"]

    def __init__(self, database_file=None):
        """
        :param str database_file: The name of a file or directory path that
            contains (or will contain) an SQLite database holding the data.
            If a directory the DEFAULT_NAME is used.
            If omitted, an unshared in-memory database will be used.
        :type database_file: str
        """
        if database_file is not None and os.listdir(database_file):
            self._path = os.path.join(database_file, DEFAULT_NAME)
        else:
            self._path = database_file
        super().__init__(
            self._path, ddl_file=_DDL_FILE, row_factory=sqlite3.Row,
            text_factory=str, case_insensitive_like=True)

    @property
    def path(self):
        """
        The path to the database file

        :rtype: str
        """
        return self._path

    def clear_ds(self):
        """ Clear all saved data but does not rerun the DDL file
        """
        with self.transaction(Isolation.EXCLUSIVE) as cursor:
            names = [row["name"] for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")]
            for name in self.META_TABLES:
                if name in names:
                    names.remove(name)
            for name in names:
                cursor.execute("DROP TABLE " + name)
            names = [row["name"] for row in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='view'")]
            for name in names:
                cursor.execute("DROP VIEW " + name)
            for name in self.META_TABLES:
                cursor.execute("DELETE FROM " + name)

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
            name = f"s{segment}_" + name
        return name

    def get_variable_map(self, segment=-1):
        """
        Gets a map of sources to a list of variables:table_type

        :param int segment: Number of the segment / reset group
        :rtype: dict(list(str))
        """
        with self.transaction() as cursor:
            variables = defaultdict(list)
            for row in cursor.execute(
                    """
                    SELECT source, variable, table_type
                    FROM metadata
                    WHERE segment = ?
                    GROUP BY source, variable, table_type
                    """, segment):
                variables[row["source"]].append(
                    f"{row['variable']}:{row['table_type']}")
            return variables

    def register_metadata(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, table_type, segment=-1):
        """
        Inserts the metadata for a source, variable segment combination

        MUST be called after update_segment

        MUST be called before an insert with the same combination.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param float sampling_interval:
            The time between timestamps. Used in the _with_interval methods
            but not checked in the with_timestamp ones
        :param str description: A description of the data source
        :param str unit:  The unit of the data
        :param int n_neurons: The total number of neurons in your source.
            No check is done between n_neurons and ids
        :param TableTypes table_type: The type of table being registered
        :param int segment: Number of the segment / reset group
        :return:
        """
        with self.transaction() as cursor:
            segment = self._clean_segment(segment)
            for row in cursor.execute(
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

            if table_type == TableTypes.MATRIX:
                data_table = None  # data_table done later if at all
            elif table_type == TableTypes.SINGLE:
                data_table = self._create_single_table(
                    source, variable, segment)
            elif table_type == TableTypes.EVENT:
                data_table = self._create_event_table(
                    source, variable, segment)
            else:
                raise NotImplementedError(
                    f"No create table for datatype {table_type}")

            cursor.execute(
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
        """
        Inserts the metadata for source, variable segment combination

        MUST be called after update_segment

        MUST be called before an insert with the same combination.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param float sampling_interval:
            The time between timestamps. Used in the _with_interval methods
            but not checked in the with_timestamp ones
        :param str description: A description of the data source
        :param str unit:  The unit of the data
        :param int n_neurons: The total number of neurons in your source.
            No check is done between n_neurons and ids
        :param int segment: Number of the segment / reset group
        :return:
        """
        self.register_metadata(
            source, variable, sampling_interval, description, unit,
            n_neurons, TableTypes.EVENT, segment)

    def register_matrix_source(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, segment=-1):
        """
        Inserts the metadata for a source, variable segment combination

        MUST be called after update_segment

        MUST be called before an insert with the same combination.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param float sampling_interval:
            The time between timestamps. Used in the _with_interval methods
            but not checked in the with_timestamp ones
        :param str description: A description of the data source
        :param str unit:  The unit of the data
        :param int n_neurons: The total number of neurons in your source.
            No check is done between n_neurons and ids
        :param int segment: Number of the segment / reset group
        :return:
        """
        self.register_metadata(
            source, variable, sampling_interval, description, unit,
            n_neurons, TableTypes.MATRIX, segment)

    def register_single_source(
            self, source, variable, sampling_interval, description, unit,
            n_neurons, segment=-1):
        """
        Inserts the metadata for a source, variable segment combination

        MUST be called after update_segment

        MUST be called before an insert with the same combination.

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param float sampling_interval:
            The time between timestamps. Used in the _with_interval methods
            but not checked in the with_timestamp ones
        :param str description: A description of the data source
        :param str unit:  The unit of the data
        :param int n_neurons: The total number of neurons in your source.
            No check is done between n_neurons and ids
        :param TableTypes table_type: The type of table being registered
        :param int segment: Number of the segment / reset group
        :return:
        """
        self.register_metadata(
            source, variable, sampling_interval, description, unit,
            n_neurons, TableTypes.SINGLE, segment)

    def _get_data_table(
            self, source, variable, segment, table_type):
        """
        Finds a data table based on source, variable and segment

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param table_type: Type of table to find or create
        :type table_type: TableTypes or None
        :return:
            The name and type of the Table.
            Name could be None if the data is too complex to get from a
            single table.
        type: (str, TableTypes) or (None, TableTypes)
        :raises:
            An Exception if an existing Table does not have the expected type
            An Exception if the table does not exists
        """
        with self.transaction() as cursor:
            for row in cursor.execute(
                    """
                    SELECT data_table, table_type
                    FROM metadata
                    WHERE source = ? AND variable = ? and segment = ?
                    LIMIT 1
                    """, (source, variable, segment)):
                if table_type:
                    assert(table_type.value == row["table_type"])
                return row["data_table"], row["table_type"]

        raise Exception(f"No Data for {source}:{variable}:{segment}")

    def _tables_by_segment(self, segment):
        """
        List the tables known for this segment

        :param int segment: Number of the segment / reset group
        :return: table names
        :type: iterable(str)
        """
        tables = set()
        views = set()
        with self.transaction() as cursor:
            for row in cursor.execute(
                    """
                    SELECT raw_table, full_view, index_table
                    FROM local_matrix_metadata
                    WHERE segment = ?
                    """, (segment, )):
                tables.add(row["data_table"])
                views.add(row["full_view"])
            for row in cursor.execute(
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
        with self.transaction() as cursor:
            # Get the column names
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            ids = [int(description[0])
                   for description in cursor.description[1:]]
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
        with self.transaction() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
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
        data_table, table_type = self._get_data_table(
            source, variable, segment, None)
        if table_type == TableTypes.MATRIX:
            return self._get_matrix_data(
                source, variable, segment, table_type)
        if table_type == TableTypes.SINGLE:
            return self._get_column_data(data_table)
        if table_type == TableTypes.EVENT:
            return self._get_events_data(data_table)

    def _clean_data(self, data, timestamps):
        """
        Does any cleaning of the input timestamps and data to the expected
        format.

        numpy arrays and iterables are converted to lists

        If timestamps is empty the first column of data is used as the
        timestamps

        It timestamps is not empty they are added as the first column of the
        data.

        The data and timestamps are converted to lists of lists as that is
        what sqllite expects

        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param data: the input data
        :type data: iterable or numpy.ndarray
        :return: The data as lists that can be used in queries
        """
        if timestamps:
            timestamps = self._make_verticle(timestamps)
            data = self._make_verticle(data)
            data = self._prepend_timestamps_to_data(data, timestamps)
            timestamps = self._to_list(timestamps)
        else:
            data = self._to_list(data)
            timestamps = [[row[0]] for row in data]
        return data, timestamps

    def _to_list(self, array):
        """
        Converts the array to a list

        :param array: a array to be converted
        :type array: iterable or numpy.ndarray
        :rtype: list
        """
        if isinstance(array, numpy.ndarray):
            return array.tolist()
        else:
            return array

    def _make_verticle(self, array):
        """
        Makes sure the array is 2 dimensional covering 1 dimensional arrays

        A list of single values is converted into a list of lists each with a
        single values.

        A 1d numpy array is is similarly converted but kept as a numpy array

        :param array: An array to be made 2D
        :type array: iterable or numpy.ndarray
        :rtpye: list or numpy.ndarray
        """
        if len(array) > 0:
            if isinstance(array, numpy.ndarray):
                if len(array.shape) == 1:
                    array.reshape(array.shape[0], 1)
                    array = array[:, None]
            else:
                array = list(array)
                if is_singleton(array[0]):
                    array = list(map(lambda x: [x], array))
        return array

    def _prepend_timestamps_to_data(self, data, timestamps):
        """
        Added the timestamps to the front of the data

        :param data: the data ar
        :type data: iterable or numpy.ndarray
        :param timestamps: The Timestamps of the data.
        :type timestamps: iterable or numpy.ndarray
        :return: list(list)
        """
        data = self._make_verticle(data)
        timestamps = self._make_verticle(timestamps)
        if isinstance(timestamps, numpy.ndarray):
            if not isinstance(data, numpy.ndarray):
                data = numpy.array(data)
            return numpy.hstack((timestamps, data)).tolist()
        return list(map(lambda x, y: x + y, timestamps, data))

    def _generate_timestamps(
            self, source, variable, segment, start_time, data):
        """
        Generates the timestamps based on the start_time, registered
            sampling_interval and the data

        The timestamps will be the same length and type as the data

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: 2d array of shape (X, len(ids)+1)
        :type data: iterable(iterable(int) or numpty.ndarray
        :param float start_time: The timestamp of the first row of data
        :param iterable(int) ids: The ids for the data.
        :param int segment: Number of the segment / reset group
        :rtype: list of numpy.array
        """
        with self.transaction() as cursor:
            for row in cursor.execute(
                    """
                    SELECT sampling_interval
                    FROM metadata
                    WHERE source = ? and variable = ? and segment = ? """,
                    (source, variable, segment)):
                sampling_interval = row["sampling_interval"]
        if isinstance(data, numpy.ndarray):
            timestamps = numpy.arange(
                start_time,  start_time + len(data) * sampling_interval,
                sampling_interval)
        else:
            timestamps = [x * sampling_interval for x in range(len(data))]
        return self._make_verticle(timestamps)

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
            f"Segment {segment} not found. Known segments are {segments.key}")

    # matrix data

    def insert_matrix_with_timestamps(
            self, source, variable, data, ids, timestamps=None, segment=-1):
        """
        Inserts matrix data into the database

        This method can be called multiple times with the same source and
        variable, and multiple distinct ids lists. The assumption is that no
        id will be in more than one of these distinct lists,
        and that the lists will be in the same order each time.

        The data will be a 2D array.
        If timtsamps is None: The first column is the timestamp
        and the one column for each id.
        Otherwise: One column for each id

        There can ever only be a single value per timestamp, id pair.

        The get methods deal with missing data so there is not requirement
        that every timestamp has data for all ids lists.

        MUST be called after the register method

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
        data, timestamps = self._clean_data(data, timestamps)
        segment = self._clean_segment(segment)
        self._insert_matrix(
            source, variable, data, ids, timestamps, segment)

    def insert_matrix_using_interval(
            self, source, variable, data, ids, start_time=0, segment=-1):
        """
        Inserts matrix data into the database

        This method can be called multiple times with the same source and
        variable, and multiple distinct ids lists. The assumption is that no
        id will be in more than one of these distinct lists,
        and that the lists will be in the same order each time.

        The data will be a 2D array with one column for each id.

        There can ever only be a single value per timestamp, id pair.

        MUST be called after the register method

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: 2d array of shape (X, len(ids)+1)
        :type data: iterable(iterable) or numpy.ndarray
        :param float start_time: The timestamp of the first row of data
        :param iterable(int) ids: The ids for the data.
        :param int segment: Number of the segment / reset group
       """
        if len(data) == 0:
            return
        segment = self._clean_segment(segment)
        timestamps = self._generate_timestamps(
            source, variable, segment, start_time, data)
        data = self._prepend_timestamps_to_data(data, timestamps)
        self._insert_matrix(
            source, variable, data, ids, timestamps, segment)

    def _insert_matrix(
            self, source, variable, data, ids, timestamps, segment):
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
        :param list(list) data: 2d array of shape (X, len(ids)+1)
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :param iterable(int) ids: The ids for the data.
        :param int segment: Number of the segment / reset group
       """
        if len(data[0]) < _MAX_COLUMNS:
            self._insert_a_matrix(source, variable, data, ids, timestamps,
                                  segment)
        else:
            for data_block, ids_block in self._split_data(data, ids):
                self._insert_a_matrix(
                    source, variable, data_block, ids_block, timestamps,
                    segment)

    def _insert_a_matrix(
            self, source, variable, data, ids, timestamps, segment):
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
        :param list(list) data: 2d array of shape (X, len(ids)+1)
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param iterable(int) ids: The ids for the data.
        :param int segment: Number of the segment / reset group
       """
        raw_table, index_table = self._get_matrix_raw_table(
            source, variable, segment, ids)

        with self.transaction() as cursor:
            # Get the number of columns
            cursor.execute(f"SELECT * FROM {raw_table} LIMIT 1")
            wildcards = ','.join('?' for _ in cursor.description)
            query = f"INSERT INTO {raw_table} VALUES ({wildcards})"
            cursor.executemany(query, data)

            query = f"INSERT OR IGNORE INTO {index_table} VALUES(?)"
            cursor.executemany(query, timestamps)

    def _get_matrix_raw_table(
            self, source, variable, segment, ids):
        """
        Get or create a raw table to store local/core matrix data in

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param int segment: Number of the segment / reset group
        :param interable(ids) ids: Ids for this ocal/core
        :return: name of raw data table
        :rtype: str
        """
        with self.transaction() as cursor:
            for row in cursor.execute(
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

        return self._create_matrix_raw_table(source, variable, segment, ids)

    def _create_matrix_raw_table(
            self,  source, variable, segment, ids):
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
        ids_str = ",".join(["'" + str(id) + "' INTEGER" for id in ids])
        ddl_statement = f"""
            CREATE TABLE IF NOT EXISTS {raw_table} 
            (timestamp FLOAT NOT NULL, 
            {ids_str})
            """
        with self.transaction() as cursor:
            cursor.execute(ddl_statement)

        index_table = self._get_matix_index_table(source, variable, segment)

        # create full view
        ddl_statement = f"""
            CREATE VIEW {full_view}
            AS SELECT * FROM {index_table} LEFT JOIN {raw_table} 
            USING (timestamp)
            """
        with self.transaction() as cursor:
            cursor.execute(ddl_statement)

            cursor.execute(
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
        ddl_statement = f"""
            CREATE TABLE IF NOT EXISTS {index_table}
            (timestamp FLOAT PRIMARY KEY ASC)
            """
        with self.transaction() as cursor:
            cursor.execute(ddl_statement)

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
        with self.transaction() as cursor:
            cursor.execute(
                """
                UPDATE metadata
                SET n_ids = n_ids + ?
                WHERE source = ? and variable = ? and segment = ?
                """,
                (n_ids, source, variable, segment))

            for row in cursor.execute(
                    """
                    SELECT n_ids FROM metadata
                    WHERE source = ? AND variable = ? and segment = ?
                    LIMIT 1
                    """, (source, variable, segment)):
                new_n_ids = row["n_ids"]

            if new_n_ids == n_ids:
                global_view = raw_table
            else:
                global_view = \
                    self._table_name(source, variable, segment) + "_all"
                ddl_statement = f"DROP VIEW IF EXISTS {global_view}"
                cursor.execute(ddl_statement)
                if new_n_ids < _MAX_COLUMNS:
                    local_views = self._get_local_views(
                        source, variable, segment)
                    ddl_statement = f"""
                        CREATE VIEW {global_view} AS SELECT * 
                        FROM {" NATURAL JOIN ".join(local_views)}"""
                    print(ddl_statement)
                    cursor.execute(ddl_statement)
                else:
                    global_view = None

            cursor.execute(
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
        with self.transaction() as cursor:
            for row in cursor.execute(
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
        data_table, _ = self._get_data_table(
            source, variable, segment, TableTypes.MATRIX)
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

        MUST be called after the register method

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: Data to store in the format timestamp, id or just id
        :type data: iterable((int, int) or iterable(int) or numpy.ndarray
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param int segment: Number of the segment / reset group
        """
        if timestamps is None:
            data = self._to_list(data)
        else:
            data = self._prepend_timestamps_to_data(data, timestamps)
        segment = self._clean_segment(segment)
        data_table, _ = self._get_data_table(
            source, variable, segment, TableTypes.EVENT)
        query = f"INSERT INTO {data_table} VALUES (?, ?)"
        with self.transaction() as cursor:
            cursor.executemany(query, data)

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
        ddl_statement = f"""
            CREATE TABLE IF NOT EXISTS {data_table} (
            timestamp FLOAT NOT NULL,
            id INTEGER NOT NULL)
            """
        with self.transaction() as cursor:
            cursor.execute(ddl_statement)
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
        data_table, _ = self._get_data_table(
            source, variable, segment, TableTypes.EVENT)
        return self._get_events_data(data_table)

    def _get_events_data(self, data_table):
        """
        Gets the events/spikes data from this table

        :param str data_table: name of table to get data from
        :return: The events data in the shape (x, 2) where the columns are
            timestamp, id
        :rtype: numpy.ndarray
        """
        with self.transaction() as cursor:
            cursor.execute(f"SELECT timestamp, id FROM {data_table}")
            return numpy.array(cursor.fetchall())

    # single data

    def insert_single(self, source, variable, data, an_id, timestamps=None,
                      segment=-1):
        """
        Inserts data where there is only a single column of local data for
        each core

        Will add columns to the table as need.

        MUST be called after the register method

        :param str source: Name of the source for example the population
        :param str variable: Name of the variable
        :param data: Data in the shape (x, 2) where the columns are
        timestamp, value
        :type data: iterable((int, int) or iterable(int) or numpy.ndarray
        :param timestamps: The Timestamps of the data.
            May be None or empty in which case the first column of data will
            be treated as the timestamps
        :type timestamps: iterable(float) or iterable(int) or
            numpy.ndarray or None
        :param int an_id: The id for this data
        :param int segment: Number of the segment / reset group
        """
        data, timestamps = self._clean_data(data, timestamps)
        segment = self._clean_segment(segment)
        data_table, _ = self._get_data_table(
            source, variable, segment, TableTypes.SINGLE)

        # Make sure a column exists for this id
        # Different cores will have different ids so no safetly needed
        ids_in_table = self._get_table_ids(data_table)

        with self.transaction() as cursor:
            if an_id not in ids_in_table:
                ddl = f"ALTER TABLE {data_table} ADD '{an_id}' INTEGER"
                cursor.execute(ddl)

            # make sure rows exist for each timestamp
            query = f"""
                INSERT or IGNORE INTO {data_table}(timestamp) 
                VALUES (?)"""
            timestamps = [[row[0]] for row in data]
            cursor.executemany(query, timestamps)

            # update the rows with the data
            query = f"""
                UPDATE {data_table} SET '{an_id}' = ? where timestamp = ?"""
            values = [[row[1], row[0]] for row in data]
            cursor.executemany(query, values)

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
        ddl_statement = f"""
            CREATE TABLE  IF NOT EXISTS {data_table} (
            timestamp FLOAT NOTE NONE)
            """
        with self.transaction() as cursor:
            cursor.execute(ddl_statement)
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
        data_table, _ = self._get_data_table(
            source, variable, segment, TableTypes.SINGLE)
        return self._get_column_data(data_table)

    def update_segment(self, segment, start_timestamp, end_timestamp):
        """
        Adds or update the information on a segment.

        If the segment was already unkown the start_timestamp must be the same.
        if the end timestamp changes all previously inserted data for this
            segment is deleted, however registered info is maintained.

        :param int segment: Number of the segment / reset group
        :param float  start_timestamp: The time of the first data row
        :param float end_timestamp: The time the simulation ran to
        """
        with self.transaction() as cursor:
            if cursor.execute(
                    """
                    INSERT OR IGNORE INTO segment_info(
                        segment, start_timestamp, end_timestamp)
                    VALUES(?,?,?)
                    """,
                    (segment, start_timestamp, end_timestamp)).rowcount == 1:
                return
            for row in cursor.execute(
                    "SELECT * FROM segment_info WHERE segment = ?",
                    (segment, )):
                assert start_timestamp == row["start_timestamp"]
                if end_timestamp > row["end_timestamp"]:
                    cursor.execute(
                        """
                            UPDATE segment_info
                            SET end_timestamp = ?
                            WHERE segment = ?
                        """, (end_timestamp, segment))
                    self._clear_segment(segment)
                elif end_timestamp < row["end_timestamp"]:
                    raise Exception(
                        f"Segment {segment} was already has an end_timestamp "
                        "of {row['end_timestamp']} so new value of "
                        "{end_timestamp} does not make sense")

    def _clear_segment(self, segment):
        """
        Deletes all data inserted for the segment but keeps registered metadata

        :param int segment: Number of the segment / reset group
        """
        tables = self._tables_by_segment(segment)
        with self.transaction() as cursor:
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")

    def get_segments(self):
        """
        Gets the info for all known segments

        :return: A dict of segment number to a tuple of
        (start_timestamp, end_timestamp)
        :rtype: dict(int, (float, float))
        """
        with self.transaction() as cursor:
            segments = dict()
            for row in cursor.execute("SELECT * FROM segment_info"):
                segments[row["segment"]] = (
                    row["start_timestamp"], row["end_timestamp"])
        return segments

    def get_source_segment_data(self, source, segment):
        """
        Gets the info for this source and segment

        :param str source: Name of the source for example the population
        :param int segment: Number of the segment / reset group
        :return:
            A dict of variable name to a dict of metadata for that variable
        :rtype: dict(str, dict(str, object))
        """
        variables = {}
        with self.transaction() as cursor:
            segment = self._clean_segment(segment)
            for row in cursor.execute(
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
                v_data["table_type"] = TableTypes(row["table_type"])
                v_data["start_timestamp"] = row["start_timestamp"]
                v_data["end_timestamp"] = row["end_timestamp"]
                variables[row["variable"]] = v_data
        return variables

    def current_segment(self):
        """
        Gets the current segment, assumed to be the highest known segment

        :return: The max known segment number
        :type: int or None
        """
        with self.transaction() as cursor:
            for row in cursor.execute(
                    "SELECT MAX(segment) AS max FROM segment_info"):
                return row["max"]
