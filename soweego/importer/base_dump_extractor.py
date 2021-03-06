#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Dump extractor abstract class"""

__author__ = 'Marco Fossati'
__email__ = 'fossati@spaziodati.eu'
__version__ = '1.0'
__license__ = 'GPL-3.0'
__copyright__ = 'Copyleft 2018, Hjfocs'


class BaseDumpExtractor:

    def extract_and_populate(self, dump_file_path: str):
        """Extract relevant data and populate SQL Alchemy entities accordingly.

        :param dump_file_path: path to a downloaded dump file
        :type dump_file_path: str
        :raises NotImplementedError: you have to override this method
        """
        raise NotImplementedError

    def get_dump_download_url(self) -> str:
        """Get the dump download URL.
        Useful if there is a way to compute the latest dump URL.

        :raises NotImplementedError: overriding this method is optional
        :return: the latest dump URL
        :rtype: str
        """
        raise NotImplementedError
