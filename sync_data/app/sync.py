# -*- coding: utf-8 -*-
# @Author  : Qliangw
# @Time    : 2022/3/4 14:45
# @Function:

import random

from sync_data.data.user_config import ConfigName
from sync_data.tool.douban import base
from sync_data.tool.douban.data.enum_data import MediaType, MediaStatus, MediaInfo
from sync_data.tool.douban.soup import parser
from sync_data.tool.douban.soup.parser import ParserHtmlText
from sync_data.tool.notion import databases
from sync_data.utils import log_detail
from sync_data.utils.config import Config


def start_sync(media_type, media_status):
    # 初始化，获取配置信息
    config_dict = Config().get_config()

    # 获取浏览器user-agent
    user_agent = config_dict[ConfigName.USER_AGENT.value]
    log_detail.info(f"【RUN】得到浏览器user-agent：{user_agent}")

    # 获取豆瓣信息
    user_id = config_dict[ConfigName.DOUBAN.value][ConfigName.DOUBAN_USER_ID.value]
    log_detail.info(f"【RUN】得到用户id：{user_id}")

    # 获取notion信息
    book_db_id = config_dict[ConfigName.NOTION.value][ConfigName.NOTION_BOOK.value]
    token = config_dict[ConfigName.NOTION.value][ConfigName.NOTION_TOKEN.value]

    # 创建一个豆瓣实例
    douban_instance = base.DouBanBase(user_agent=user_agent)
    log_detail.debug("【RUN】创建一个豆瓣实例")

    start_number = 1

    while True:
        page_number = int(start_number / 15 + 1)
        # 获取html
        html_text = douban_instance.get_html_text(user_id=user_id,
                                                  media_type=media_type,
                                                  media_status=media_status,
                                                  start_number=start_number)
        log_detail.info(f"【RUN】访问第{page_number}页数据完成")


        # 创建一个解析实例
        info_instance = ParserHtmlText(html_text)
        # 获取全部url
        url_list = info_instance.get_url_list()
        url_num = len(url_list)
        log_detail.info(f"【RUN】本页有{url_num}个媒体")
        for url in url_list:
            # 随机休眠5-10秒钟
            time_number = random.randint(5, 10)
            log_detail.info(f"【RUN】随机休眠时间5-10s，本次休眠：{time_number}s")

            html_text = douban_instance.get_html_text(url=url,
                                                      user_id=user_id,
                                                      media_type=MediaType.BOOK.value,
                                                      media_status=MediaStatus.WISH.value)
            # 创一个详情页实例
            html_parser = parser.ParserHtmlText(html_text=html_text)
            # 解析详情页，获取数据字典
            html_dict = html_parser.get_parser_dict(MediaType.BOOK.value)

            # 添加url
            html_dict[MediaInfo.URL.value] = url

            databases.update_database(data_dict=html_dict,
                                      database_id=book_db_id,
                                      token=token)
        log_detail.info(f"【RUN】完成第{page_number}页媒体数据库的导入！")
        if url_num > 14:
            start_number += 15
        else:
            break
    log_detail.info(f"【RUN】所有信息已导入notion！,共计导入{(page_number-1)*15+len(url_list)}条数据")

