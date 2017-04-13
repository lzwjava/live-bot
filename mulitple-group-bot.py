#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *
import redis
import sys

logger = WXBot.init_logger()


class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.apply_failed = False
        self.auto_add_friend = True
        logger.info(sys.argv)
        if len(sys.argv) > 1:
            if sys.argv[1] == 'disable-add':
                self.auto_add_friend = False
                logger.info('disable add')
        self.mid = None
        self.group_keywords = [u'人工智能', u'设计', u'前端', u'后端', u'iOS', u'创业', u'产品', u'运营', u'互联网']
        self.group_names = [u'人工智能大部落', u'设计大部落', u'前端大部落', u'后端大部落', u'iOS大部落',
                            u'创业大部落', u'产品大部落', u'运营大部落', u'互联网大部落']

    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 37:
            RecommendInfo = msg['content']['data']
            username = RecommendInfo['UserName']
            nickname = RecommendInfo['NickName']
            if not self.auto_add_friend:
                return
            if self.apply_failed:
                logger.error('already apply failed')
                return
            apply_res = self.apply_useradd_requests(RecommendInfo)
            if not apply_res:
                self.apply_failed = True
                return
            self.add_count = self.add_count + 1
            logger.info('auto add user %s count: %d' % (nickname, self.add_count))
        elif msg['msg_type_id'] == 3:
            # known group
            pass
        elif msg['msg_type_id'] == 4 or msg['msg_type_id'] == 99:
            username = msg['user']['id']
            content = msg['content']
            if content['type'] == 0:
                if content['data'].find(u'群') != -1:
                    if self.check_if_not_in_group(username):
                        self.send_poster_msg(username)
                else:
                    text = content['data']
                    if text in self.group_keywords:
                        if self.check_if_not_in_group(username):
                            index = self.group_keywords.index(text)
                            group_name = self.group_names[index]
                            self.add_group(username, group_name)
            elif content['type'] == 3:
                pass
                # self.add_group(username)
        elif msg['msg_type_id'] == 12:
            pass
            # self.batch_get_group_members()
        elif msg['msg_type_id'] == 10000:
            user_id = msg['user']['id']
            if user_id[:1] == '@' and user_id[1:2] != '@':
                # single chat
                content = msg['content']['data']
                if content.find(u'你已添加') != -1:
                    user_id = msg['user']['id']
                    time.sleep(1)
                    self.send_poster_msg(user_id, u'嗨，很高兴认识朋友~~趣直播创始人一枚~~感谢对趣直播的支持~~')
                    logger.info('auto send msg 10000')
                elif content.find(u'收到红包') != -1:
                    logger.info('receive packet')
            elif user_id[:2] == '@@':
                content = msg['content']['data']
                if content.find(u'加入了群聊') != -1:
                    logger.info('batch_get_group_members')
                    self.batch_get_target_group_members(user_id)
        elif msg['msg_type_id'] == 1:
            pass

    def check_if_not_in_group(self, username):
        group_name = self.group_of_friend(username)
        if group_name:
            self.send_msg_by_uid(u'朋友已经在%s群里啦' % (group_name), username)
            return False
        else:
            return True

    def group_of_friend(self, uid):
        for group_name in self.group_names:
            if self.is_friend_in_group(uid, group_name):
                return group_name
        return None

    def send_failed_msg(self, user_id):
        self.send_msg_by_uid('抱歉 加群失败 请等待我的主人来手工处理~~', user_id)

    def send_poster_msg(self, user_id, extra_msg=u''):
        self.send_msg_by_uid(u'请回复关键词来加入趣直播的相关群，结交更多同行小伙伴。'
                             u'\n回复「人工智能」来加入人工智能群\n回复「设计」来加入设计群\n回复「前端」来加入前端群\n'
                             u'回复「后端」来加入后端群\n回复「iOS」来加入iOS群\n回复「创业」来加入创业者群\n'
                             u'回复「产品」来加入产品群\n回复「运营」来加入运营群\n回复「互联网」来加入互联网群。只能加入一个群哟，选择最合适的群哈。', user_id)

    def add_group(self, username, group_username):
        if self.is_friend_in_group(username, group_username):
            logger.info('already in group skip')
            self.send_msg_by_uid(u'朋友已经在群里啦 感谢', username)
        else:
            add_result = self.add_friend_to_group(username, group_username)
            if add_result:
                logger.info('auto invite %s to group' % username)
                self.send_msg_by_uid(u'感谢朋友加群，请进群改备注公司-职位-姓名哈，也可介绍自己，发个红包和大家熟悉一下~~', username)
            else:
                logger.error('fail to add friend to group')
                self.send_failed_msg(username)

    def have_group_in_list(self, group_name):
        for group in self.group_list:
            if group['NickName'] == group_name:
                return True
        return False

    def check_groups(self):
        have_target_group = True
        for group_name in self.group_names:
            if not self.have_group_in_list(group_name):
                have_target_group = False
                logger.error('not have target group name: %s', group_name)
                break
        if not have_target_group:
            raise Exception('not have target group')

    def ready(self):
        self.mid = self.upload_media('poster.jpg', True)
        if self.mid is None:
            raise Exception('mid is none')
        logger.info('mid is %s', self.mid)

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
    bot.use_merge = False
    bot.run()


if __name__ == '__main__':
    main()
