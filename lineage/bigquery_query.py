from typing import Optional
from lineage.query_context import QueryContext
from sqllineage.exceptions import SQLLineageException
from lineage.table_resolver import TableResolver
from lineage.query import Query
from lineage.utils import get_logger

logger = get_logger(__name__)


class BigQueryQuery(Query):

    EMPTY_QUERY_TYPE = ''
    DROP_PREFIX = 'DROP'
    ALTER_PREFIX = 'ALTER'
    PLATFORM_TYPE = 'BIGQUERY'

    @staticmethod
    def from_dict(query_dict: dict):
        query_context = QueryContext.from_dict(query_dict.pop('query_context'))
        if 'platform_type' in query_dict:
            query_dict.pop('platform_type')
        return BigQueryQuery(**query_dict, query_context=query_context)

    @staticmethod
    def _parse_table_json_column(table_resolver: TableResolver, table_json_column: dict) -> Optional[str]:
        if table_json_column is None:
            return None

        project = table_json_column.get('project_id')
        dataset = table_json_column.get('dataset_id')
        table = table_json_column.get('table_id')

        if project is None or dataset is None or table is None:
            return None

        if table.startswith('anon'):
            return None

        return table_resolver.name_qualification(f'{project}.{dataset}.{table}')

    def parse(self, full_table_names: bool = False) -> None:
        try:
            table_resolver = TableResolver(profile_database_name=self._profile_database_name,
                                           profile_schema_name=self._profile_schema_name,
                                           full_table_names=full_table_names)

            target_table = self._parse_table_json_column(table_resolver, self._query_context.destination_table)
            source_tables = set()
            for referenced_table in self._query_context.referenced_tables:
                source_table = self._parse_table_json_column(table_resolver, referenced_table)
                source_tables.add(source_table)

            query_type = self.EMPTY_QUERY_TYPE
            if self._query_context.query_type is not None:
                query_type = self._query_context.query_type

            if query_type.startswith(self.DROP_PREFIX):
                self.dropped_tables.add(target_table)
            elif query_type.startswith(self.ALTER_PREFIX):
                _, _, self.renamed_tables, _ = \
                    self._parse_query_text(table_resolver, self._raw_query_text)
            else:
                self.source_tables = source_tables
                self.target_tables.add(target_table)
        except SQLLineageException as exc:
            logger.debug(f'SQLLineageException was raised while parsing this query -\n{self._raw_query_text}\n'
                         f'Error was -\n{exc}.')

