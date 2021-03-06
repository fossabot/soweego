#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Set of Wikidata vocabulary terms."""

__author__ = 'Marco Fossati'
__email__ = 'fossati@spaziodati.eu'
__version__ = '1.0'
__license__ = 'GPL-3.0'
__copyright__ = 'Copyleft 2018, Hjfocs'

# Sandbox items in production site
SANDBOX_1 = 'Q4115189'
SANDBOX_2 = 'Q13406268'
SANDBOX_3 = 'Q15397819'

# Properties used to get instances
INSTANCE_OF = 'P31'
OCCUPATION = 'P106'

# Properties used for references
STATED_IN = 'P248'
RETRIEVED = 'P813'

# Target catalog items
DISCOGS = 'Q504063'
IMDB = 'Q37312'
MUSICBRAINZ = 'Q14005'
TWITTER = 'Q918'

# Identifier properties
DISCOGS_ARTIST_PID = 'P1953'
IMDB_PID = 'P345'
MUSICBRAINZ_ARTIST_PID = 'P434'
TWITTER_USERNAME_PID = 'P2002'
FACEBOOK_PID = 'P2013'

# Widely used generic property to hold URLs
DESCRIBED_AT_URL = 'P973'
OFFICIAL_WEBSITE = 'P856'

# Entity classes handled by soweego
ACTOR = 'Q33999'
BAND = 'Q215380'
FILM_DIRECTOR = 'Q2526255'
FILM_PRODUCER = 'Q3282637'
HUMAN = 'Q5'
MUSICIAN = 'Q639669'

# Target catalogs helper dictionary
CATALOG_MAPPING = {
    'discogs': {
        'qid': DISCOGS,
        'pid': DISCOGS_ARTIST_PID
    },
    'imdb': {
        'qid': IMDB,
        'pid': IMDB_PID
    },
    'musicbrainz': {
        'qid': MUSICBRAINZ,
        'pid': MUSICBRAINZ_ARTIST_PID
    },
    'twitter': {
        'qid': TWITTER,
        'pid': TWITTER_USERNAME_PID
    }
}

# Properties with URL data type, from SPARQL query:
# SELECT ?property WHERE { ?property a wikibase:Property ; wikibase:propertyType wikibase:Url . }
URL_PIDS = set([
    'P854', 'P855', 'P856', 'P953', 'P963', 'P968', 'P973', 'P1019', 'P1065',
    'P1324', 'P1325', 'P1348', 'P1401', 'P1421', 'P1482', 'P1581', 'P1613',
    'P1628', 'P1709', 'P1713', 'P1896', 'P1957', 'P1991', 'P2035', 'P2078',
    'P2235', 'P2236', 'P2488', 'P2520', 'P2649', 'P2699', 'P2888', 'P3254',
    'P3268', 'P3950', 'P4001', 'P4238', 'P4570', 'P4656', 'P4765', 'P4945',
    'P4997', 'P5178', 'P5195', 'P5282', 'P5305', 'P5715'
])

# Properties for metadata-based validation: gender, birth/death date/place
PLACE_OF_BIRTH = 'P19'
PLACE_OF_DEATH = 'P20'
SEX_OR_GENDER = 'P21'
DATE_OF_BIRTH = 'P569'
DATE_OF_DEATH = 'P570'
METADATA_PIDS = set([PLACE_OF_BIRTH, PLACE_OF_DEATH,
                     SEX_OR_GENDER, DATE_OF_BIRTH, DATE_OF_DEATH])
