from neurocard_lib.common import CsvTable
import os
import numpy as np
import collections
import csv
from neurocard_lib import utils

class STATSBenchmark(object):
    ALIAS_TO_TABLE_NAME = {
        'b': 'badges',
        'v': 'votes',
        'ph': 'postHistory',
        'p': 'posts',
        'u': 'users',
        'c': 'comments',
        'pl': 'postLinks',
        't': 'tags'
    }
    CSV_FILES = [
        'badges.csv', 'votes.csv', 'postHistory.csv', 'posts.csv',
        'users.csv', 'comments.csv', 'postLinks.csv', 'tags.csv'
    ]
    BASE_TABLE_PRED_COLS=collections.defaultdict(
        list,
        {
            'badges.csv':['Id', 'UserId', 'Date'],
            'votes.csv':['Id', 'PostId', 'VoteTypeId', 'CreationDate', 'UserId','BountyAmount'], 
            'postHistory.csv':['Id', 'PostHistoryTypeId', 'PostId', 'CreationDate','UserId'], 
            'posts.csv':['Id', 'PostTypeId', 'CreationDate',
                                                'Score', 'ViewCount', 'OwnerUserId',
                                                'AnswerCount', 'CommentCount', 'FavoriteCount',
                                                'LastEditorUserId'],
            'users.csv':['Id', 'Reputation', 'CreationDate', 'Views', 'UpVotes', 'DownVotes'], 
            'comments.csv':['Id', 'PostId', 'Score', 'CreationDate', 'UserId'], 
            'postLinks.csv':['Id', 'PostId', 'Score', 'CreationDate', 'UserId'], 
            'tags.csv':['Id', 'Count', 'ExcerptPostId']
        })
    # _CONTENT_COLS = None

    # @staticmethod
    # def ContentColumns():
    #     if STATSBenchmark._CONTENT_COLS is None:
    #         STATSBenchmark._CONTENT_COLS = {
    #             '{}.csv'.format(table_name):
    #             range_cols + STATSBenchmark.CATEGORICAL_COLUMNS[table_name]
    #             for table_name, range_cols in
    #             STATSBenchmark.RANGE_COLUMNS.items()
    #         }
    #         # Add join keys.
    #         for table_name in STATSBenchmark._CONTENT_COLS:
    #             cols = STATSBenchmark._CONTENT_COLS[table_name]
    #             if table_name == 'title.csv':
    #                 cols.append('id')
    #             elif 'movie_id' in STATSBenchmark.BASE_TABLE_PRED_COLS[
    #                     table_name]:
    #                 cols.append('movie_id')

    #     return STATSBenchmark._CONTENT_COLS
    @staticmethod
    def GetSTATSJoinKeys():
        return {
            'badges':['Id','UserId'],
            'votes':['Id','PostId','UserId'],
            'postHistory':['Id','PostId','UserId'],
            'posts':['Id','OwnerUserId'],
            'users':['Id'],
            'comments':['Id','PostId','UserId'],
            'postLinks':['Id','PostId','RelatedPostId'],
            'tags':['Id','ExcerptPostId']
        }


def LoadSTATS(table=None,
             data_dir='./datasets/stats/',
             try_load_parsed=True,
             use_cols='all'):
    """Loads STATS tables with a specified set of columns.

    use_cols:
      
      None: load all columns

    Returns:
      A single CsvTable if 'table' is specified, else a dict of CsvTables.
    """
    assert use_cols in ['all',None], use_cols

    def TryLoad(table_name, filepath, use_cols, **kwargs):
        """Try load from previously parsed (table, columns)."""
        if use_cols:
            cols_str = '-'.join(use_cols)
            parsed_path = filepath[:-4] + '.{}.table'.format(cols_str)
        else:
            parsed_path = filepath[:-4] + '.table'
        if try_load_parsed:
            if os.path.exists(parsed_path):
                arr = np.load(parsed_path, allow_pickle=True)
                print('Loaded parsed Table from', parsed_path)
                table = arr.item()
                # print(table)
                return table
        table = CsvTable(
            table_name,
            filepath,
            cols=use_cols,
            **kwargs,
        )
        if try_load_parsed:
            np.save(open(parsed_path, 'wb'), table)
            print('Saved parsed Table to', parsed_path)
        return table

    def get_use_cols(filepath):
        if use_cols == 'all':
            return STATSBenchmark.BASE_TABLE_PRED_COLS.get(filepath, None)
        # elif use_cols == 'content':
        #     return JoinOrderBenchmark.ContentColumns().get(filepath, None)
        # elif use_cols == 'multi':
        #     return JoinOrderBenchmark.JOB_M_PRED_COLS.get(filepath, None)
        # elif use_cols == 'full':
        #     return JoinOrderBenchmark.JOB_FULL_PRED_COLS.get(filepath, None)
        return None  # Load all.

    if table:
        filepath = table + '.csv'
        table = TryLoad(
            table,
            data_dir + filepath,
            use_cols=get_use_cols(filepath),
            type_casts={},
            escapechar='\\',
        )
        return table

    tables = {}
    for filepath in STATSBenchmark.BASE_TABLE_PRED_COLS:
        tables[filepath[0:-4]] = TryLoad(
            filepath[0:-4],
            data_dir + filepath,
            use_cols=get_use_cols(filepath),
            type_casts={},
            escapechar='\\',
        )

    return tables



def STATSToQuery(csv_file, use_alias_keys=True):
    """Parses custom #-delimited query csv.

    `use_alias_keys` only applies to the 2nd return value.
    If use_alias_keys is true, join_dict will use aliases (t, mi) as keys;
    otherwise it uses real table names (title, movie_index).

    Converts into (tables, join dict, predicate dict, true cardinality).  Only
    works for single equivalency class.
    """
    queries = []
    with open(csv_file) as f:
        data_raw = list(list(rec) for rec in csv.reader(f, delimiter='#'))
        for row in data_raw:
            reader = csv.reader(row)  # comma-separated
            table_dict =utils._get_table_dict(next(reader))
            # print(table_dict)
            join_dict =utils._get_join_dict(next(reader), table_dict, use_alias_keys)
            # print(join_dict)
            predicate_dict = utils._get_predicate_dict(next(reader), table_dict)
            # print(predicate_dict)
            true_cardinality = int(next(reader)[0])
            queries.append((list(table_dict.values()), join_dict,
                            predicate_dict, true_cardinality))
    
    return queries