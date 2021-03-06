#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Validation of Wikidata statements against a target catalog"""

__author__ = 'Marco Fossati'
__email__ = 'fossati@spaziodati.eu'
__version__ = '1.0'
__license__ = 'GPL-3.0'
__copyright__ = 'Copyleft 2018, Hjfocs'

import json
import logging
from collections import defaultdict

import click
from soweego.commons import target_database
from soweego.commons.constants import HANDLED_ENTITIES, TARGET_CATALOGS
from soweego.commons.data_gathering import (extract_ids_from_urls,
                                            gather_identifiers,
                                            gather_relevant_pids,
                                            gather_target_links,
                                            gather_target_metadata,
                                            gather_wikidata_links,
                                            gather_wikidata_metadata)
from soweego.commons.db_manager import DBManager
from soweego.importer.models.base_entity import BaseEntity
from soweego.importer.models.musicbrainz_entity import (MusicbrainzArtistEntity,
                                                        MusicbrainzBandEntity)
from soweego.ingestor import wikidata_bot
from soweego.wikidata import sparql_queries, vocabulary

LOGGER = logging.getLogger(__name__)


@click.command()
@click.argument('wikidata_query', type=click.Choice(['class', 'occupation']))
@click.argument('class_qid')
@click.argument('catalog_pid')
@click.argument('catalog', type=click.Choice(target_database.available_targets()))
@click.argument('entity_type', type=click.Choice(target_database.available_types()))
@click.option('-o', '--outfile', type=click.File('w'), default='output/non_existent_ids.json', help="default: 'output/non_existent_ids.json'")
def check_existence_cli(wikidata_query, class_qid, catalog_pid, catalog, entity_type, outfile):
    """Check the existence of identifier statements.

    Dump a JSON file of invalid ones ``{identifier: QID}``
    """
    try:
        entity = target_database.get_entity(catalog, entity_type)
    except:
        LOGGER.error('Not able to retrive entity for given database_table')

    invalid = check_existence(wikidata_query, class_qid,
                              catalog_pid, entity)
    json.dump(invalid, outfile, indent=2)


def check_existence(class_or_occupation_query, class_qid, catalog_pid, entity: BaseEntity):
    query_type = 'identifier', class_or_occupation_query
    session = DBManager.connect_to_db()
    invalid = defaultdict(set)
    count = 0

    for result in sparql_queries.run_identifier_or_links_query(query_type, class_qid, catalog_pid, 0):
        for qid, target_id in result.items():
            results = session.query(entity).filter(
                entity.catalog_id == target_id).all()
            if not results:
                LOGGER.warning(
                    '%s identifier %s is invalid', qid, target_id)
                invalid[target_id].add(qid)
                count += 1

    LOGGER.info('Total invalid identifiers = %d', count)
    # Sets are not serializable to JSON, so cast them to lists
    return {target_id: list(qids) for target_id, qids in invalid.items()}


@click.command()
@click.argument('entity', type=click.Choice(HANDLED_ENTITIES.keys()))
@click.argument('catalog', type=click.Choice(TARGET_CATALOGS.keys()))
@click.option('--wikidata-dump/--no-wikidata-dump', default=False, help='Dump links gathered from Wikidata. Default: no.')
@click.option('--upload/--no-upload', default=True, help='Upload check results to Wikidata. Default: yes.')
@click.option('--sandbox/--no-sandbox', default=False, help='Upload to the Wikidata sandbox item Q4115189. Default: no.')
@click.option('-c', '--cache', type=click.File(), default=None, help="Load Wikidata links previously dumped via '-w'. Default: no.")
@click.option('-d', '--deprecated', type=click.File('w'), default='output/links_deprecated_ids.json', help="Default: 'output/links_deprecated_ids.json'")
@click.option('-e', '--ext-ids', type=click.File('w'), default='output/external_ids_to_be_added.tsv', help="Default: 'output/external_ids_to_be_added.tsv'")
@click.option('-u', '--urls', type=click.File('w'), default='output/urls_to_be_added.tsv', help="Default: 'output/urls_to_be_added.tsv'")
@click.option('-w', '--wikidata', type=click.File('w'), default='output/wikidata_links.json', help="Default: 'output/wikidata_links.json'")
def check_links_cli(entity, catalog, wikidata_dump, upload, sandbox, cache, deprecated, ext_ids, urls, wikidata):
    """Check the validity of identifier statements based on the available links.

    Dump 3 output files:

    1. catalog identifiers to be deprecated, as a JSON ``{identifier: [QIDs]}``;

    2. external identifiers to be added, as a TSV ``QID  identifier_PID  identifier``;

    3. URLs to be added, as a TSV ``QID  P973   URL``.
    """
    if cache is None:
        to_deprecate, ext_ids_to_add, urls_to_add, wikidata_links = check_links(
            entity, catalog)
    else:
        wikidata_cache = _load_wikidata_cache(cache)
        to_deprecate, ext_ids_to_add, urls_to_add, wikidata_links = check_links(
            entity, catalog, wikidata_cache)

    if wikidata_dump:
        json.dump({qid: {data_type: list(values) for data_type, values in data.items()}
                   for qid, data in wikidata_links.items()}, wikidata, indent=2, ensure_ascii=False)
        LOGGER.info('Wikidata links dumped to %s', wikidata.name)
    if upload:
        _upload_links(catalog, to_deprecate, urls_to_add,
                      ext_ids_to_add, sandbox)

    json.dump({target_id: list(qids) for target_id,
               qids in to_deprecate.items()}, deprecated, indent=2)
    ext_ids.writelines(
        ['\t'.join(triple) + '\n' for triple in ext_ids_to_add])
    urls.writelines(
        ['\t'.join(triple) + '\n' for triple in urls_to_add])
    LOGGER.info('Result dumped to %s, %s, %s', deprecated.name,
                ext_ids.name, urls.name)


def check_links(entity, catalog, wikidata_cache=None):
    catalog_terms = _get_vocabulary(catalog)

    # Target links
    target = gather_target_links(entity, catalog)
    # Early stop in case of no target links
    if target is None:
        return None, None, None

    to_deprecate = defaultdict(set)
    to_add = defaultdict(set)

    if wikidata_cache is None:
        wikidata = {}

        # Wikidata links
        gather_identifiers(entity, catalog, catalog_terms['pid'], wikidata)
        url_pids, ext_id_pids_to_urls = gather_relevant_pids()
        gather_wikidata_links(wikidata, url_pids, ext_id_pids_to_urls)
    else:
        wikidata = wikidata_cache

    # Check
    _assess('links', wikidata, target, to_deprecate, to_add)

    # Separate external IDs from URLs
    ext_ids_to_add, urls_to_add = extract_ids_from_urls(
        to_add, ext_id_pids_to_urls)

    LOGGER.info('Validation completed. %d %s IDs to be deprecated, %d external IDs to be added, %d URL statements to be added', len(
        to_deprecate), catalog, len(ext_ids_to_add), len(urls_to_add))

    return to_deprecate, ext_ids_to_add, urls_to_add, wikidata


@click.command()
@click.argument('entity', type=click.Choice(HANDLED_ENTITIES.keys()))
@click.argument('catalog', type=click.Choice(TARGET_CATALOGS.keys()))
@click.option('--wikidata-dump/--no-wikidata-dump', default=False, help='Dump metadata gathered from Wikidata. Default: no.')
@click.option('--upload/--no-upload', default=True, help='Upload check results to Wikidata. Default: yes.')
@click.option('--sandbox/--no-sandbox', default=False, help='Upload to the Wikidata sandbox item Q4115189. Default: no.')
@click.option('-c', '--cache', type=click.File(), default=None, help="Load Wikidata metadata previously dumped via '-w'. Default: no.")
@click.option('-d', '--deprecated', type=click.File('w'), default='output/metadata_deprecated_ids.json', help="Default: 'output/metadata_deprecated_ids.json'")
@click.option('-a', '--added', type=click.File('w'), default='output/statements_to_be_added.tsv', help="Default: 'output/statements_to_be_added.tsv'")
@click.option('-w', '--wikidata', type=click.File('w'), default='output/wikidata_metadata.json', help="Default: 'output/wikidata_metadata.json'")
def check_metadata_cli(entity, catalog, wikidata_dump, upload, sandbox, cache, deprecated, added, wikidata):
    """Check the validity of identifier statements based on the availability
    of the following metadata: birth/death date, birth/death place, gender.

    Dump 2 output files:

    1. catalog identifiers to be deprecated, as a JSON ``{identifier: [QIDs]}``;

    2. statements to be added, as a TSV ``QID  metadata_PID  value``;
    """
    if cache:
        wikidata_cache = _load_wikidata_cache(cache)
        to_deprecate, to_add, wikidata_metadata = check_metadata(
            entity, catalog, wikidata_cache)
    else:
        to_deprecate, to_add, wikidata_metadata = check_metadata(
            entity, catalog)

    if wikidata_dump:
        json.dump({qid: {data_type: list(values) for data_type, values in data.items()}
                   for qid, data in wikidata_metadata.items()}, wikidata, indent=2, ensure_ascii=False)
        LOGGER.info('Wikidata metadata dumped to %s', wikidata.name)
    if upload:
        _upload(catalog, to_deprecate, to_add, sandbox)

    if to_deprecate:
        json.dump({target_id: list(qids) for target_id,
                   qids in to_deprecate.items()}, deprecated, indent=2)
    if to_add:
        added.writelines(
            ['\t'.join(triple) + '\n' for triple in to_add])

    LOGGER.info('Result dumped to %s, %s',
                deprecated.name, added.name)


def check_metadata(entity, catalog, wikidata_cache=None):
    catalog_terms = _get_vocabulary(catalog)

    # Target metadata
    target = gather_target_metadata(entity, catalog)
    # Early stop in case of no target metadata
    if target is None:
        return None, None, None

    to_deprecate = defaultdict(set)
    to_add = defaultdict(set)

    if wikidata_cache is None:
        wikidata = {}

        # Wikidata metadata
        gather_identifiers(entity, catalog, catalog_terms['pid'], wikidata)
        gather_wikidata_metadata(wikidata)
    else:
        wikidata = wikidata_cache

    # Check
    _assess('metadata', wikidata, target, to_deprecate, to_add)

    return to_deprecate, to_add, wikidata


def _load_wikidata_cache(file_handle):
    raw_cache = json.load(file_handle)
    LOGGER.info("Loaded Wikidata cache from '%s'", file_handle.name)
    cache = {}
    for qid, data in raw_cache.items():
        for data_type, value_list in data.items():
            # Metadata has values that are a list
            if isinstance(value_list[0], list):
                value_set = set()
                for value in value_list:
                    value_set.add(tuple(value))
                if cache.get(qid):
                    cache[qid][data_type] = value_set
                else:
                    cache[qid] = {data_type: value_set}
            else:
                if cache.get(qid):
                    cache[qid][data_type] = set(value_list)
                else:
                    cache[qid] = {data_type: set(value_list)}
    return cache


def _assess(criterion, source, target_iterator, to_deprecate, to_add):
    LOGGER.info('Starting check against target %s ...', criterion)
    target = _consume_target_iterator(target_iterator)
    # Large loop size = # given Wikidata class instances with identifiers, e.g., 80k musicians
    for qid, data in source.items():
        source_data = data.get(criterion)
        if not source_data:
            LOGGER.warning(
                'Skipping check: no %s available in QID %s', criterion, qid)
            continue
        identifiers = data['identifiers']
        # 1 or tiny loop size = # of identifiers per Wikidata item (should always be 1)
        for target_id in identifiers:
            if target_id in target.keys():
                target_data = target.get(target_id)
                if not target_data:
                    LOGGER.warning(
                        'Skipping check: no %s available in target ID %s', criterion, target_id)
                    continue
                shared = source_data.intersection(target_data)
                extra = target_data.difference(source_data)
                if not shared:
                    LOGGER.debug(
                        'No shared %s between %s and %s. The identifier statement will be deprecated', criterion, qid, target_id)
                    to_deprecate[target_id].add(qid)
                else:
                    LOGGER.debug('%s and %s share these %s: %s',
                                 qid, target_id, criterion, shared)
                if extra:
                    LOGGER.debug(
                        '%s has extra %s that will be added to %s: %s', target_id, criterion, qid, extra)
                    to_add[qid].update(extra)
                else:
                    LOGGER.debug('%s has no extra %s', target_id, criterion)
    LOGGER.info('Check against target %s completed: %d IDs to be deprecated, %d statements to be added',
                criterion, len(to_deprecate), len(to_add))


def _consume_target_iterator(target_iterator):
    target = defaultdict(set)
    for identifier, *data in target_iterator:
        if len(data) == 1:  # Links
            target[identifier].add(data.pop())
        else:  # Metadata
            target[identifier].add(tuple(data))
    return target


def _get_vocabulary(catalog):
    catalog_terms = vocabulary.CATALOG_MAPPING.get(catalog)
    if not catalog_terms:
        raise ValueError('Bad catalog: %s. Please use one of %s' %
                         (catalog, vocabulary.CATALOG_MAPPING.keys()))
    return catalog_terms


def _upload_links(catalog, to_deprecate, urls_to_add, ext_ids_to_add, sandbox):
    catalog_qid = _upload(catalog, to_deprecate, urls_to_add, sandbox)
    LOGGER.info('Starting addition of external IDs to Wikidata ...')
    wikidata_bot.add_statements(ext_ids_to_add, catalog_qid, sandbox)


def _upload(catalog, to_deprecate, to_add, sandbox):
    catalog_terms = _get_vocabulary(catalog)
    catalog_qid = catalog_terms['qid']
    LOGGER.info('Starting deprecation of %s IDs ...', catalog)
    wikidata_bot.delete_or_deprecate_identifiers(
        'deprecate', to_deprecate, catalog, sandbox)
    LOGGER.info('Starting addition of statements to Wikidata ...')
    wikidata_bot.add_statements(to_add, catalog_qid, sandbox)
    return catalog_qid
