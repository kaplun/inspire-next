# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2015 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Manage migration from INSPIRE legacy instance."""

from __future__ import print_function

import os
import sys

from flask import current_app
from flask.ext.script import prompt_bool

from invenio_ext.es import es
from invenio_ext.script import Manager
from invenio_ext.sqlalchemy import db

from .tasks import migrate, migrate_broken_records

manager = Manager(description=__doc__)


@manager.option('--records', '-r', dest='records',
                action='append',
                default=None,
                help='Specific record IDs to migrate.')
@manager.option('--collection', '-c', dest='collections',
                action='append',
                default=None,
                help='Specific collections to migrate.')
@manager.option('--input', '-f', dest='file_input',
                help='Specific collections to migrate.')
@manager.option('--remigrate', '-m', action='store_true', dest='remigrate',
                default=False, help='Try to remigrate broken records')
@manager.option('-t', '--input-type', dest='input_type', default='marcxml',
                help="Format of input file.")
@manager.option('--force', action='store_true', dest='force_import', default=None,
                help="Force records that are not registered to import on the system")
@manager.option('--broken-output', '-b', dest='broken_output', default=None,
                help='Where to write back records that were not possible to migrate')
@manager.option('--dry-run', '-d', action='store_true', dest='dry_run', default=False,
                help='Whether records should really be imported or not')
def populate(records, collections, file_input=None, remigrate=False,
             input_type=None, force_import=None, broken_output=None,
             dry_run=False):
    """Populates the system with records

    Usage: inveniomanage migrator populate -f prodsync20151117173222.xml.gz \
                --force --broken-output=/tmp/broken.xml:
    """
    if records is None and collections is None:
        # We harvest all
        print("Migrating all records...", file=sys.stderr)
    if records:
        print("Migrating records: {0}".format(",".join(records)))
    if collections:
        print("Migrating collections: {0}".format(",".join(collections)))

    if remigrate:
        print("Remigrate broken records...")
        migrate_broken_records.delay(broken_output=broken_output, dry_run=dry_run)

    elif file_input and not os.path.isfile(file_input):
        print("{0} is not a file!".format(file_input), file=sys.stderr)

    elif file_input:
        print("Migrating records from file: {0}".format(file_input))

        migrate.delay(os.path.abspath(file_input), broken_output=broken_output,
                      dry_run=dry_run)
    else:
        legacy_base_url = current_app.config.get("CFG_INSPIRE_LEGACY_BASEURL")
        print(
            "Migrating records from {0}".format(
                legacy_base_url
            ),
            file=sys.stderr
        )

        job = migrate.delay(legacy_base_url,
                            records=records,
                            collections=collections,
                            file_input=file_input,
                            broken_output=broken_output,
                            dry_run=dry_run)
        print("Scheduled migration job {0}".format(job.id))


@manager.command
def remove_bibxxx():
    """Drop all the legacy bibxxx tables."""
    drop_tables("bib%%x")


@manager.command
def remove_idx():
    """Drop all the legacy BibIndex tables."""
    drop_tables('idx%%')
    drop_tables('tmp_idx%%')


@manager.command
def remove_others():
    """Drop misc legacy tables."""
    drop_tables('aid%%')
    drop_tables('bsk%%')
    drop_tables('rnk%%')
    drop_tables('jrn%%')
    drop_tables('sbm%%')
    drop_tables('swr%%')
    drop_tables('crc%%')


@manager.command
def remove_legacy_tables():
    """Remove all legacy tables."""
    db.session.begin(subtransactions=True)
    try:
        db.engine.execute("SET FOREIGN_KEY_CHECKS=0;")
        remove_others()
        remove_bibxxx()
        remove_idx()
        db.engine.execute("SET FOREIGN_KEY_CHECKS=1;")
        db.session.commit()
    except Exception as err:  # noqa
        db.session.rollback()
        current_app.logger.exception(err)


def recreate_index(name, mapping):
    """Recreate an ElasticSearch index."""
    es.indices.delete(index=name + "_v1", ignore=404)
    es.indices.create(index=name + "_v1", body=mapping)
    es.indices.put_alias(index=name + "_v1", name=name)


@manager.command
def create_indices():
    """Create or recreate the indices for records and holdingpen."""
    import json

    from invenio.base.globals import cfg
    from invenio_search.registry import mappings

    indices = set(cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"].values())
    indices.add(cfg['SEARCH_ELASTIC_DEFAULT_INDEX'])
    for index in indices:
        mapping = {}
        mapping_filename = index + ".json"
        if mapping_filename in mappings:
            mapping = json.load(open(mappings[mapping_filename], "r"))
        recreate_index(index, mapping)
        # Create Holding Pen index
        if mapping:
            mapping['mappings']['record']['properties'].update(
                cfg['WORKFLOWS_HOLDING_PEN_ES_PROPERTIES']
            )
        name = cfg['WORKFLOWS_HOLDING_PEN_ES_PREFIX'] + index
        recreate_index(name, mapping)


@manager.command
def delete_indices():
    """Delete all the indices for records and holdingpen."""
    from invenio.base.globals import cfg

    indices = set(cfg["SEARCH_ELASTIC_COLLECTION_INDEX_MAPPING"].values())
    indices.add(cfg['SEARCH_ELASTIC_DEFAULT_INDEX'])
    holdingpen_indices = [
        cfg['WORKFLOWS_HOLDING_PEN_ES_PREFIX'] + name for name in list(indices)
    ]
    indices.update(holdingpen_indices)
    for index in indices:
        es.indices.delete(index=index, ignore=404)


@manager.command
def clean_records():
    """Truncate all the records from various tables."""
    from sqlalchemy.engine import reflection

    print('>>> Truncating all records.')

    tables_to_truncate = [
        "bibrec",
        "record_json",
    ]
    db.session.begin(subtransactions=True)
    try:
        db.engine.execute("SET FOREIGN_KEY_CHECKS=0;")

        # Grab any table with foreign keys to bibrec for truncating
        inspector = reflection.Inspector.from_engine(db.engine)
        for table_name in inspector.get_table_names():
            for foreign_key in inspector.get_foreign_keys(table_name):
                if foreign_key["referred_table"] == "bibrec":
                    tables_to_truncate.append(table_name)

        if not prompt_bool("Going to truncate: {0}".format(
                "\n".join(tables_to_truncate))):
            return
        for table in tables_to_truncate:
            db.engine.execute("TRUNCATE TABLE {0}".format(table))
            print(">>> Truncated {0}".format(table))

        db.engine.execute("DELETE FROM pidSTORE WHERE pid_type='recid'")
        print(">>> Truncated pidSTORE WHERE pid_type='recid'")

        db.engine.execute("SET FOREIGN_KEY_CHECKS=1;")
        db.session.commit()
    except Exception as err:  # noqa
        db.session.rollback()
        current_app.logger.exception(err)


def drop_tables(table_filter):
    """Drop tables helper."""
    table_names = db.engine.execute(
        "SELECT TABLE_NAME"
        " FROM INFORMATION_SCHEMA.TABLES"
        " WHERE TABLE_NAME LIKE '{0}'"
        " AND table_schema='{1}'".format(
            table_filter,
            current_app.config.get('CFG_DATABASE_NAME')
        )
    ).fetchall()
    for table in table_names:
        db.engine.execute("DROP TABLE {0}".format(table[0]))
        print(">>> Dropped {0}.".format(table[0]))
    print(">>> Removed {0} tables.".format(len(table_names)))
