#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""MusicBrainz SQL Alchemy ORM model"""

__author__ = 'Massimo Frasson'
__email__ = 'maxfrax@gmail.com'
__version__ = '1.0'
__license__ = 'GPL-3.0'
__copyright__ = 'Copyleft 2018, MaxFrax96'

from soweego.importer.models.base_entity import BaseEntity, BaseRelationship
from soweego.importer.models.base_link_entity import BaseLinkEntity
from sqlalchemy import (Column, ForeignKey, Index, String, Table,
                        UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

BASE = declarative_base()
ARTIST_TABLE = 'musicbrainz_artist'
ARTIST_LINK_TABLE = 'musicbrainz_artist_link'
BAND_TABLE = 'musicbrainz_band'
BAND_LINK_TABLE = 'musicbrainz_band_link'
ARTIST_BAND_RELATIONSHIP_TABLE = "musicbrainz_artist_band_relationship"


class MusicbrainzArtistEntity(BaseEntity):
    __tablename__ = ARTIST_TABLE
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'concrete': True}

    gender = Column(String(10))
    birth_place = Column(String(255), nullable=True)
    death_place = Column(String(255), nullable=True)


class MusicbrainzBandEntity(BaseEntity):
    __tablename__ = BAND_TABLE
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'concrete': True}

    birth_place = Column(String(255), nullable=True)
    death_place = Column(String(255), nullable=True)


class MusicbrainzArtistLinkEntity(BaseLinkEntity):
    __tablename__ = ARTIST_LINK_TABLE
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'concrete': True}


class MusicbrainzBandLinkEntity(BaseLinkEntity):
    __tablename__ = BAND_LINK_TABLE
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'concrete': True}

# NOTICE: both catalog_ids of this entity can be both in Artist and Band table


class MusicBrainzArtistBandRelationship(BaseRelationship):
    __tablename__ = ARTIST_BAND_RELATIONSHIP_TABLE

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'concrete': True}

    def __repr__(self):
        return super().__repr__()
