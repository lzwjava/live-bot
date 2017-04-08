#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *
import redis

logger = WXBot.init_logger()


class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.redis_obj = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.add_count = 0
        self.apply_failed = False
        self.wechatGroups = []

    def save_recommend_info(self, username, recommend_info):
        ok = self.redis_obj.hset('recommend_infos', username, json.dumps(recommend_info))
        if ok:
            logger.info('save recommend_info %s' % username)
        else:
            logger.error('save failed %s' % username)

    def save_group_recommend_info(self, username, recommend_info):
        return self.redis_obj.hset('group_recommend_infos', username, json.dumps(recommend_info))

    def get_group_recommend_info(self, username):
        return self.redis_obj.hget('group_recommend_infos', username)

    def get_recommend_info(self, username):
        return self.redis_obj.hget('recommend_infos', username)

    def clean_nickname(self, nickname):
        if nickname.find('span') != -1:
            return ''
        else:
            return nickname

    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 37:
            RecommendInfo = msg['content']['data']
            username = RecommendInfo['UserName']
            nickname = RecommendInfo['NickName']
            if self.apply_failed:
                logger.error('already apply failed')
                self.save_recommend_info(username, RecommendInfo)
                return
            apply_res = self.apply_useradd_requests(RecommendInfo)
            if not apply_res:
                logger.error('apply failed %s' % (nickname))
                self.save_recommend_info(username, RecommendInfo)
                self.apply_failed = True
                return
            self.add_count = self.add_count + 1
            logger.info('auto add user %s count: %d' % (nickname, self.add_count))
            # self.send_poster_msg(username, u'嗨,很高兴认识朋友~~小弟创业狗一枚~~感谢对趣直播的支持~~')
        elif msg['msg_type_id'] == 3:
            # known group
            pass
        elif msg['msg_type_id'] == 4 or msg['msg_type_id'] == 99:
            # self.send_remark_tip(msg)
            username = msg['user']['id']
            nickname = msg['user']['name']
            content = msg['content']
            if content['type'] == 0:
                if content['data'].find(u'群') != -1:
                    self.send_poster_msg(username)
                elif content['data'].find(u'测试') != -1:
                    self.send_msg_to_group(username)
            elif content['type'] == 3:
                self.add_group(username, nickname)
        elif msg['msg_type_id'] == 12:
            pass
            # self.batch_get_group_members()
        elif msg['msg_type_id'] == 10000:
            user_id = msg['user']['id']
            if user_id[:1] == '@' and user_id[1:2] != '@':
                # single chat
                content = msg['content']['data']
                if content.find(u'现在可以开始聊天了') != -1:
                    user_id = msg['user']['id']
                    time.sleep(3)
                    self.send_poster_msg(user_id, u'嗨,很高兴认识朋友~~小弟创业狗一枚~~感谢对趣直播的支持~~')
                    logger.info('auto send msg 10000')
                elif content.find(u'收到红包') != -1:
                    logger.info('receive packet')
            elif user_id[:2] == '@@':
                content = msg['content']['data']
                if content.find(u'通过扫描你分享的二维码加入群聊') != -1:
                    self.check_group_and_send(user_id)

        elif msg['msg_type_id'] == 1:
            pass

    def check_group_and_send(self, group_id):
        group = self.get_group_contact(group_id)
        nickname = group['NickName']
        member_count = len(group['MemberList'])
        wechatGroup = self.get_group_by_name(nickname)
        if (wechatGroup is not None):
            logger.info('is our group')
            if member_count % 5 == 0:
                self.send_msg_to_group(group_id)
        else:
            logger.info('not our group')

    def get_group_by_name(self, nickname):
        for wechatGroup in self.wechatGroups:
            if wechatGroup['groupUserName'] == nickname:
                return wechatGroup
        return None

    def is_our_group(self, nickname):
        for wechatGroup in self.wechatGroups:
            if wechatGroup['groupUserName'] == nickname:
                return True
        return False

    def send_msg_to_group(self, group_id):
        self.send_msg_by_uid(u"请大家加我微信进互联网交流群哈, 大群里有嘉宾们, 同行们~~~如果已经是好友, 请私信我「加群」来加入哈", group_id)
        self.send_img_msg_by_uid('poster.jpg', group_id)

    def send_poster_msg(self, user_id, extra_msg=u''):
        self.send_msg_by_uid((extra_msg + u'请转发海报到朋友圈，配上文字(可自行修改), 并发送截图过来，'
                                          u'来加入趣直播互联网交流群哈~~大群里有大咖、同行们，名额有限，感谢支持~~'),
                             user_id)
        self.send_msg_by_uid(u'我决定加入「趣直播互联网交流群」, 和大咖们一起聊产品，聊思维，长见识!', user_id)
        self.send_img_msg_by_uid('poster.jpg', user_id)

    def add_group(self, username, nickname):
        group_username = u'互联网交流大群'
        if (self.is_friend_in_group(username, group_username)):
            logger.info('already in group skip %s' % (nickname))
            self.send_msg_by_uid(u'朋友已经在群里啦 感谢', username)
        else:
            add_result = self.add_friend_to_group(username, group_username)
            if add_result:
                logger.info('auto invite %s to group' % nickname)
                self.send_msg_by_uid(u'感谢朋友转发,请保留24小时哈,请进群改备注公司-职位-姓名哈 也可介绍自己, 发个红包和大家熟悉一下~~', username)
            else:
                logger.error('fail to add friend to group')
                self.send_msg_by_uid(u'感谢朋友支持 一会批量拉群哈', username)

    def ready(self):
        self.wechatGroups = self.get_all_api_group()
        for group in self.group_list:
            logger.info(group['NickName'])
            is_our_group = self.is_our_group(group['NickName'])
            logger.info('is our group ' + str(is_our_group))

    def get_all_api_group(self):
        res = self.base_get_api_server('wechatGroups')
        if res['status'] == 'success':
            return res['result']
        else:
            raise Exception('get group failed')


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.run()


if __name__ == '__main__':
    main()
