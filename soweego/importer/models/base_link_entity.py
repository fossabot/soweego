#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Base SQL Alchemy ORM link entity"""

__author__ = 'Marco Fossati'
__email__ = 'fossati@spaziodati.eu'
__version__ = '1.0'
__license__ = 'GPL-3.0'
__copyright__ = 'Copyleft 2018, Hjfocs'


from sqlalchemy import Boolean, Column, Index, Integer, String
from sqlalchemy.ext.declarative import (AbstractConcreteBase, declarative_base,
                                        declared_attr)

BASE = declarative_base()


class BaseLinkEntity(AbstractConcreteBase, BASE):
    __tablename__ = None
    internal_id = Column(Integer, unique=True,
                         primary_key=True, autoincrement=True)
    # Catalog identifier of the entity having the link, indexed
    catalog_id = Column(String(50), nullable=False, index=True)
    # Full URL
    url = Column(String(255))
    # Whether the URL is a Wiki link
    is_wiki = Column(Boolean)
    # Tokenized URL
    tokens = Column(String(255))

    @declared_attr
    def __table_args__(cls):
        return (
            Index('ftix_tokens_%s' % cls.__tablename__,
                  "tokens", mysql_prefix="FULLTEXT"),
            {'mysql_charset': 'utf8mb4'}
        )

    def __repr__(self) -> str:
        return "<BaseLinkEntity(catalog_id='{0}', url='{1}')>".format(self.catalog_id, self.url)
