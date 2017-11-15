# -*- coding: utf-8 -*-
import json
from scrapy.spider import Request,Spider
from zhihuuser.items import ZhihuuserItem


class ZhihuSpider(Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['https://www.zhihu.com/']
    start_user = 'excited-vczh'

    #伪造初始用户连接和请求参数
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    url_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    #伪造关注人的请求连接和请求参数
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    #伪造被关注此用户的连接和请求参数
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        '''
        1、伪造用户请求url
        2、伪造请求关注人的url
        3、伪造请求被关注人的url
        :return:
        '''
        yield Request(self.user_url.format(user=self.start_user,include=self.url_query),callback=self.parse_user)
        yield Request(self.user_url.format(user=self.start_user,include=self.follows_query),callback=self.parse_follows)
        yield Request(self.user_url.format(user=self.start_user,include=self.followers_query),callback=self.parse_followers)

    def parse_user(self, response):
        '''
        1、获取每个用户的详细信息
        2、返回给Items
        3、
        :param response:
        :return:
        '''
        result = json.loads(response.text)
        item = ZhihuuserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        #起始用户的关注列表的每个用户关注列表
        yield Request(self.follows_url.format(user=result.get('url_token'),include=self.follows_query,limit=20,offset=0),self.parse_follows)
        #起始用户的被关注列表的每个用户的关注列表
        yield Request(self.followers_url.format(user=result.get('url_token'),include=self.followers_query,limit=20,offset=0),self.parse_followers)

    def parse_follows(self, response):
        '''
        1、关注的用户详细信息（其实这里只要url_token，一遍于callback拿到他的相信信息）
        2、分页
        :param response:
        :return:
        '''
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.url_query),callback=self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,self.parse_follows)

    def parse_followers(self, response):
        '''
        1、关注他的人
        2、同样拿到这个人的详细信息（其实就是要这个人的url_token信息，以便于拿到他的相信信息）
        2、分页
        :param response:
        :return:
        '''
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.url_query),callback=self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,self.parse_followers)