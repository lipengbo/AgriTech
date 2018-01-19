# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from django.db import models


class AgritechItem(scrapy.Item):
    # define the fields for your item here like:
    key_val = scrapy.Field()
    db_title = scrapy.Field()

    def get_sql(self):
        sql = """INSERT INTO `chartsite`.`{0}`({1}) VALUES ({2}) ON DUPLICATE KEY UPDATE  `索引`=VALUES(`索引`)"""
        keyy = ""
        valuess = """"""
        for k, v in self['key_val'].items():
            keyy += "`{}`, ".format(k)
            if v:
                valuess += '''"{}", '''.format(v.replace('"', "'"))
            else:
                valuess += '''" ", '''
        if "作物种类" not in keyy and "农作物名优特新品种数据库" in self['db_title']:
            keyy += "`{}`, ".format("作物种类")
            valuess += '''"", '''
        # try:
        #     dupkey = list(self['key_val'])[1]
        # except:
        #     dupkey = ""
        sql = sql.format(self["db_title"], keyy[:-2], valuess[:-2])

        return sql


class AgritechcodeItem(scrapy.Item):
    # define the fields for your item here like:
    db_code = scrapy.Field()
    item_code = scrapy.Field()
    db_title = scrapy.Field()
    allpage = scrapy.Field()
    page = scrapy.Field()
    codes = scrapy.Field()
