# -*- coding: utf-8 -*-
import re
import os
import scrapy
import pickle

from scrapy import Request, FormRequest, Spider
from urllib.parse import urljoin
from fake_useragent import UserAgent
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from AgriTeach.items import AgriteachItem
from scrapy_redis.spiders import RedisSpider


class AgritechSpider(Spider):

    name = 'AgriTech'
    redis_key = "AgriTech:start_urls"
    allowed_domains = ['stb.agridata.cn']
    start_urls = ['http://stb.agridata.cn/Site/Home/Default.aspx']
    list_url = "http://stb.agridata.cn/Site/DataTable/List.aspx"
    detail_url = "http://stb.agridata.cn/Site/DataTable/Detail.aspx?MenuId=-1&DataCategoryGId="

    def parse(self, response):
        db_urls = response.xpath('//*[@class="LeftList"]/ul/li/a')
        for db_url in db_urls:
            url = db_url.xpath("@href").extract_first()
            db_title = db_url.xpath("text()").extract_first()
            if "农业科技文摘数据库" in db_title:
                url = urljoin(response.url, url)
                db_code = url.split("DataCategoryGId=")[-1]
                yield Request(url=url,
                              dont_filter=True,
                              callback=self.parse_page,
                              meta={"db_title": db_title,
                                    'db_code': db_code
                                    }
                              )

    def parse_page(self, response):
        db_code = response.meta.get("db_code", "")
        allpage = response.css("#PageSplitBottom > tr > th:nth-child(2)::text").extract_first()
        VIEWSTATE = response.css("#__VIEWSTATE::attr(value)").extract_first()
        EVENTVALIDATION = response.css("#__EVENTVALIDATION::attr(value)").extract_first()
        VIEWSTATEGENERATOR = response.css("#__VIEWSTATEGENERATOR::attr(value)").extract_first()
        allpage = int(allpage[4:].replace(" 页", ""))
        data = {
            "__VIEWSTATE": VIEWSTATE,
            "__VIEWSTATEGENERATOR": VIEWSTATEGENERATOR,
            "__EVENTVALIDATION": EVENTVALIDATION,
            "PageSplitBottom$ImageButtonNext.x": "5",
            "PageSplitBottom$ImageButtonNext.y": "9",
            "DropDownListRowCount": "10",
            "PageSplitBottom$ImageButtonGoto.x": '4',
            "PageSplitBottom$ImageButtonGoto.y": '6',
        }
        for page in range(1, allpage + 1):
            data["PageSplitBottom$textBoxPageSize"] = str(page)
            headers = {
                "User-Agent": getattr(UserAgent(), 'random')
            }
            yield FormRequest(
                url=response.url,
                headers=headers,
                formdata=data,
                callback=self.parse_detail_code,
                meta={"db_title": response.meta.get("db_title", ""),
                      'db_code': db_code,
                      'allpage': allpage,
                      'page': page}
            )

    def parse_detail_code(self, response):
        codes = response.css(".ListContent1.EllipsisTable a::attr(onclick)").extract()
        codes = [i.replace("ShowDetail('", "").replace("')", "") for i in codes]
        for code in codes:
            payloads = {"HiddenGId": code}
            headers = {
                "User-Agent": getattr(UserAgent(), 'random')
            }
            yield FormRequest(
                url=self.detail_url + response.meta.get("db_code", ""),
                headers=headers,
                formdata=payloads,
                callback=self.parse_detail,
                meta={"db_title": response.meta.get("db_title", ""),
                      "code": code
                      }
            )

    def parse_detail(self, response):
        items = AgriteachItem()
        node = response.css("div.List table tr")
        items['key_val'] = {}
        items['db_title'] = response.meta.get("db_title", "").replace("、", "")
        items['key_val']['索引'] = response.meta.get("code", "")
        for i in node:
            key = i.css("th::text").extract_first()
            value = i.css("td::text").extract_first()
            items['key_val'][key] = value
        yield items

