#  Copyright (c) 2010 Franz Allan Valencia See
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
from robot.api import logger


class Query(object):
    """
    Query handles all the querying done by the Database Library.
    """

    def query(self, selectStatement, sansTran=False, returnAsDict=False):
        """
        Uses the input `selectStatement` to query for the values that will be returned as a list of tuples. Set optional
        input `sansTran` to True to run command without an explicit transaction commit or rollback.
        Set optional input `returnAsDict` to True to return values as a list of dictionaries.

        Tip: Unless you want to log all column values of the specified rows,
        try specifying the column names in your select statements
        as much as possible to prevent any unnecessary surprises with schema
        changes and to easily see what your [] indexing is trying to retrieve
        (i.e. instead of `"select * from my_table"`, try
        `"select id, col_1, col_2 from my_table"`).

        For example, given we have a table `person` with the following data:
        | id | first_name  | last_name |
        |  1 | Franz Allan | See       |

        When you do the following:
        | @{queryResults} | Query | SELECT * FROM person |
        | Log Many | @{queryResults} |

        You will get the following:
        [1, 'Franz Allan', 'See']

        Also, you can do something like this:
        | ${queryResults} | Query | SELECT first_name, last_name FROM person |
        | Log | ${queryResults[0][1]}, ${queryResults[0][0]} |

        And get the following
        See, Franz Allan

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | @{queryResults} | Query | SELECT * FROM person | True |
        """
        cur = None
        try:
            cur = self._dbconnection.cursor()
            logger.info('Executing : Query  |  %s ' % selectStatement)
            self.__execute_sql(cur, selectStatement)
            allRows = cur.fetchall()

            if returnAsDict:
                mappedRows = []
                col_names = [c[0] for c in cur.description]

                for rowIdx in range(len(allRows)):
                    d = {}
                    for colIdx in range(len(allRows[rowIdx])):
                        d[col_names[colIdx]] = allRows[rowIdx][colIdx]
                    mappedRows.append(d)
                return mappedRows

            return allRows
        finally:
            if cur:
                if not sansTran:
                    self._dbconnection.rollback()

    def row_count(self, selectStatement, sansTran=False):
        """
        Uses the input `selectStatement` to query the database and returns the number of rows from the query. Set
        optional input `sansTran` to True to run command without an explicit transaction commit or rollback.

        For example, given we have a table `person` with the following data:
        | id | first_name  | last_name |
        |  1 | Franz Allan | See       |
        |  2 | Jerry       | Schneider |

        When you do the following:
        | ${rowCount} | Row Count | SELECT * FROM person |
        | Log | ${rowCount} |

        You will get the following:
        2

        Also, you can do something like this:
        | ${rowCount} | Row Count | SELECT * FROM person WHERE id = 2 |
        | Log | ${rowCount} |

        And get the following
        1

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | ${rowCount} | Row Count | SELECT * FROM person | True |
        """
        cur = None
        try:
            cur = self._dbconnection.cursor()
            logger.info('Executing : Row Count  |  %s ' % selectStatement)
            self.__execute_sql(cur, selectStatement)
            data = cur.fetchall()
            if self.db_api_module_name in ["sqlite3", "ibm_db", "ibm_db_dbi", "pyodbc"]:
                rowCount = len(data)
            else:
                rowCount = cur.rowcount
            return rowCount
        finally:
            if cur:
                if not sansTran:
                    self._dbconnection.rollback()

    def description(self, selectStatement, sansTran=False):
        """
        Uses the input `selectStatement` to query a table in the db which will be used to determine the description. Set
        optional input `sansTran` to True to run command without an explicit transaction commit or rollback.

        For example, given we have a table `person` with the following data:
        | id | first_name  | last_name |
        |  1 | Franz Allan | See       |

        When you do the following:
        | @{queryResults} | Description | SELECT * FROM person |
        | Log Many | @{queryResults} |

        You will get the following:
        [Column(name='id', type_code=1043, display_size=None, internal_size=255, precision=None, scale=None, null_ok=None)]
        [Column(name='first_name', type_code=1043, display_size=None, internal_size=255, precision=None, scale=None, null_ok=None)]
        [Column(name='last_name', type_code=1043, display_size=None, internal_size=255, precision=None, scale=None, null_ok=None)]

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | @{queryResults} | Description | SELECT * FROM person | True |
        """
        cur = None
        try:
            cur = self._dbconnection.cursor()
            logger.info('Executing : Description  |  %s ' % selectStatement)
            self.__execute_sql(cur, selectStatement)
            description = list(cur.description)
            if sys.version_info[0] < 3:
                for row in range(0, len(description)):
                    description[row] = (description[row][0].encode('utf-8'),) + description[row][1:]
            return description
        finally:
            if cur:
                if not sansTran:
                    self._dbconnection.rollback()

    def delete_all_rows_from_table(self, tableName, sansTran=False):
        """
        Delete all the rows within a given table. Set optional input `sansTran` to True to run command without an
        explicit transaction commit or rollback.

        For example, given we have a table `person` in a database

        When you do the following:
        | Delete All Rows From Table | person |

        If all the rows can be successfully deleted, then you will get:
        | Delete All Rows From Table | person | # PASS |
        If the table doesn't exist or all the data can't be deleted, then you
        will get:
        | Delete All Rows From Table | first_name | # FAIL |

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | Delete All Rows From Table | person | True |
        """
        cur = None
        selectStatement = ("DELETE FROM %s" % tableName)
        try:
            cur = self._dbconnection.cursor()
            logger.info('Executing : Delete All Rows From Table  |  %s ' % selectStatement)
            result = self.__execute_sql(cur, selectStatement)
            if result is not None:
                if not sansTran:
                    self._dbconnection.commit()
                return result
            if not sansTran:
                self._dbconnection.commit()
        finally:
            if cur:
                if not sansTran:
                    self._dbconnection.rollback()

    def execute_sql_script(self, sqlScriptFileName, sansTran=False):
        """
        Executes the content of the `sqlScriptFileName` as SQL commands. Useful for setting the database to a known
        state before running your tests, or clearing out your test data after running each a test. Set optional input
        `sansTran` to True to run command without an explicit transaction commit or rollback.

        
        Sample usage :
        | Execute Sql Script | ${EXECDIR}${/}resources${/}DDL-setup.sql |
        | Execute Sql Script | ${EXECDIR}${/}resources${/}DML-setup.sql |
        | #interesting stuff here |
        | Execute Sql Script | ${EXECDIR}${/}resources${/}DML-teardown.sql |
        | Execute Sql Script | ${EXECDIR}${/}resources${/}DDL-teardown.sql |

        SQL commands are expected to be delimited by a semi-colon (';') - they will be executed separately.

        For example:
        DELETE FROM person_employee_table;
        DELETE FROM person_table;
        DELETE FROM employee_table;

        Also, the last SQL command can optionally omit its trailing semi-colon.

        For example:
        DELETE FROM person_employee_table;
        DELETE FROM person_table;
        DELETE FROM employee_table

        Given this, that means you can create spread your SQL commands in several
        lines.

        For example:
        DELETE
          FROM person_employee_table;
        DELETE
          FROM person_table;
        DELETE
          FROM employee_table

        However, lines that starts with a number sign (`#`) or a double dash ("--")
        are treated as a commented line. Thus, none of the contents of that line will be executed.


        For example:
        # Delete the bridging table first...
        DELETE
          FROM person_employee_table;
          # ...and then the bridged tables.
        DELETE
          FROM person_table;
        DELETE
          FROM employee_table

        The slash signs ("/") are always ignored and have no impact on execution order.

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | Execute Sql Script | ${EXECDIR}${/}resources${/}DDL-setup.sql | True |
        """
        with open(sqlScriptFileName, encoding='UTF-8') as sql_file:
            cur = None
            try:
                statements_to_execute = []
                cur = self._dbconnection.cursor()
                logger.info('Executing : Execute SQL Script  |  %s ' % sqlScriptFileName)
                current_statement = ''
                inside_statements_group = False

                for line in sql_file:
                    line = line.strip()
                    if line.startswith('#') or line.startswith('--') or line == "/":
                        continue
                    if line.lower().startswith("begin"):
                        inside_statements_group = True
                    
                    # semicolons inside the line? use them to separate statements
                    # ... but not if they are inside a begin/end block (aka. statements group)
                    sqlFragments = line.split(';')
                    
                    # no semicolons
                    if len(sqlFragments) == 1:
                        current_statement += line + ' '
                        continue
                    
                    # "select * from person;" -> ["select..", ""]
                    for sqlFragment in sqlFragments:
                        sqlFragment = sqlFragment.strip()
                        if len(sqlFragment) == 0:
                            continue
                        if inside_statements_group:
                            # if statements inside a begin/end block have semicolns,
                            # they must persist - even with oracle
                            sqlFragment += "; "
                        if sqlFragment.lower() == "end; ":
                            inside_statements_group = False
                        elif sqlFragment.lower().startswith("begin"):
                            inside_statements_group = True
                        current_statement += sqlFragment
                        if not inside_statements_group:
                            statements_to_execute.append(current_statement.strip())
                            current_statement = ''

                current_statement = current_statement.strip()
                if len(current_statement) != 0:
                    statements_to_execute.append(current_statement)
                    
                for statement in statements_to_execute:
                    logger.info(f"Executing statement from script file: {statement}")
                    omit_semicolon = not statement.lower().endswith("end;")
                    self.__execute_sql(cur, statement, omit_semicolon)
                if not sansTran:
                    self._dbconnection.commit()
            finally:
                if cur:
                    if not sansTran:
                        self._dbconnection.rollback()

    def execute_sql_string(self, sqlString, sansTran=False):
        """
        Executes the sqlString as SQL commands. Useful to pass arguments to your sql. Set optional input `sansTran` to
        True to run command without an explicit transaction commit or rollback.

        SQL commands are expected to be delimited by a semi-colon (';').

        For example:
        | Execute Sql String | DELETE FROM person_employee_table; DELETE FROM person_table |

        For example with an argument:
        | Execute Sql String | SELECT * FROM person WHERE first_name = ${FIRSTNAME} |

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | Execute Sql String | DELETE FROM person_employee_table; DELETE FROM person_table | True |
        """
        cur = None
        try:
            cur = self._dbconnection.cursor()
            logger.info('Executing : Execute SQL String  |  %s ' % sqlString)
            self.__execute_sql(cur, sqlString)
            if not sansTran:
                self._dbconnection.commit()
        finally:
            if cur:
                if not sansTran:
                    self._dbconnection.rollback()

    def call_stored_procedure(self, spName, spParams=None, sansTran=False):
        """
        Uses the inputs of `spName` and 'spParams' to call a stored procedure. Set optional input `sansTran` to
        True to run command without an explicit transaction commit or rollback.

        spName should be the stored procedure name itself
        spParams [Optional] should be a List of the parameters being sent in.  The list can be one or multiple items.

        The return from this keyword will always be a list.

        Example:
        | @{ParamList} = | Create List | FirstParam | SecondParam | ThirdParam |
        | @{QueryResults} = | Call Stored Procedure | DBName.SchemaName.StoredProcName | List of Parameters |

        Example:
        | @{ParamList} = | Create List | Testing | LastName |
        | Set Test Variable | ${SPName} = | DBTest.DBSchema.MyStoredProc |
        | @{QueryResults} = | Call Stored Procedure | ${SPName} | ${ParamList} |
        | Log List | @{QueryResults} |

        Using optional `sansTran` to run command without an explicit transaction commit or rollback:
        | @{QueryResults} = | Call Stored Procedure | DBName.SchemaName.StoredProcName | List of Parameters | True |
        """
        if spParams is None:
            spParams = []
        cur = None
        try:
            if self.db_api_module_name == "pymssql":
                cur = self._dbconnection.cursor(as_dict=False)
            else:
                cur = self._dbconnection.cursor()
            PY3K = sys.version_info >= (3, 0)
            if not PY3K:
                spName = spName.encode('ascii', 'ignore')
            logger.info('Executing : Call Stored Procedure  |  %s  |  %s ' % (spName, spParams))
            cur.callproc(spName, spParams)
            cur.nextset()
            retVal=list()
            for row in cur:
                #logger.info ( ' %s ' % (row))
                retVal.append(row)
            if not sansTran:
                self._dbconnection.commit()
            return retVal
        finally:
            if cur:
                if not sansTran:
                    self._dbconnection.rollback()

    def __execute_sql(self, cur, sql_statement, omit_trailing_semicolon=None):
        """
        Runs the `sql_statement` using `cur` as Cursor object.
        Use `omit_trailing_semicolon` parameter (bool) for explicite instruction,
        if the trailing semicolon (;) should be removed - otherwise the statement
        won't be executed by some databases (e.g. Oracle).
        Otherwise it's decided based on the current database module in use.
        """
        if omit_trailing_semicolon is None:
            omit_trailing_semicolon = self.omit_trailing_semicolon
        if omit_trailing_semicolon:
            sql_statement = sql_statement.rstrip(";")
        logger.debug(f"Executing sql: {sql_statement}")
        return cur.execute(sql_statement)
