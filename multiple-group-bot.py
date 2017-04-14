#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *
import redis
import sys

logger = WXBot.init_logger('multiple-group-bot')


class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.apply_failed = False
        self.auto_add_friend = True
        self.add_count = 0
        logger.info(sys.argv)
        if len(sys.argv) > 1:
            if sys.argv[1] == 'disable-add':
                self.auto_add_friend = False
                logger.info('disable add')
        self.mid = None
        self.group_keywords = [u'人工智能', u'设计', u'前端', u'后端', u'iOS', u'Android', u'创业', u'产品', u'运营', u'互联网']
        self.group_names = [u'人工智能大部落', u'产品运营设计大部落', u'前端大部落', u'后端大部落', u'iOS大部落', u'Android大部落',
                            u'创业大部落', u'产品运营设计大部落', u'产品运营设计大部落', u'互联网交流大群']
        self.contact_index = 0
        self.remark_time = 0

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
                text = content['data']
                self.handle_receive_text(text, username)
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
                    self.send_poster_msg(user_id, u'嗨，很高兴认识朋友~~趣直播创始人一枚~~感谢对趣直播的支持~~\n')
                    logger.info('auto send msg 10000')
                elif content.find(u'收到红包') != -1:
                    logger.info('receive packet')
            elif user_id[:2] == '@@':
                content = msg['content']['data']
                if content.find(u'加入了群聊') != -1:
                    logger.info('batch_get_group_members')
                    self.batch_get_target_group_members(user_id)
        elif msg['msg_type_id'] == 1:
            content = msg['content']
            username = msg['to_user_id']
            if content['type'] == 0:
                text = content['data']
                self.handle_text_invite(text, username, True)

    def handle_receive_text(self, text, username):
        if text.find(u'群') != -1:
            if self.check_can_add_group(username):
                self.send_poster_msg(username)
        elif text == u'更新':
            logger.info('begin update members')
            self.batch_get_group_members()
            logger.info('end update members')
        elif text.find(u'退出') != -1:
            self.handle_exit(username)
        else:
            self.handle_text_invite(text, username, True)

    def handle_exit(self, username):
        group_usernames = self.group_of_friend(username)
        for group_username in group_usernames:
            group = self.get_group_by_nickname(group_username)
            self.batch_get_target_group_members(group['UserName'])
        self.send_msg_by_uid(u'棒棒哒，现在试试发送关键词加入新的群~~', username)

    def handle_text_invite(self, text, username, strict=False):
        text = text.strip().lower()
        for group_keyword in self.group_keywords:
            lower_keyword = group_keyword.lower()
            matched = False
            if not strict and text.find(lower_keyword) != -1:
                matched = True
            elif strict and text == lower_keyword:
                matched = True
            if matched:
                if self.check_can_add_group(username):
                    index = self.group_keywords.index(group_keyword)
                    group_name = self.group_names[index]
                    self.add_group(username, group_name)
                    return

    def check_can_add_group(self, username):
        groups = self.group_of_friend(username)
        if len(groups) >= 1:
            self.send_msg_by_uid(u'最多只能加一个群哟，朋友已经在%s里啦，如果真想加，可先退出原来的群，'
                                 u'并回复「退出」两字告诉我你退出啦' %
                                 groups[0], username)
            return False
        else:
            return True

    def group_of_friend(self, uid):
        groups = []
        for group_name in self.group_names:
            if self.is_friend_in_group(uid, group_name):
                if group_name not in groups:
                    groups.append(group_name)
        return groups

    def send_failed_msg(self, user_id):
        self.send_msg_by_uid('抱歉 加群失败 请等待我的主人来手工处理~~', user_id)

    def send_poster_msg(self, user_id, extra_msg=u''):
        self.send_msg_by_uid(u'%s请回复关键词来加入趣直播的相关群，结交更多同行小伙伴。\n'
                             u'回复「人工智能」来加入人工智能群\n回复「设计」来加入设计群\n回复「前端」来加入前端群\n'
                             u'回复「后端」来加入后端群\n回复「iOS」来加入iOS群\n回复「Android」来加入Android群\n回复「创业」来加入创业者群\n'
                             u'回复「产品」来加入产品群\n回复「运营」来加入运营群\n回复「互联网」来加入互联网群。\n\n最多只能加入一个群哟，请选择最合适的群~~' % extra_msg,
                             user_id)

    def add_group(self, username, group_username):
        if self.is_friend_in_group(username, group_username):
            logger.info('already in group skip')
            self.send_msg_by_uid(u'朋友已经在群里啦 感谢', username)
        else:
            add_result = self.add_friend_to_group(username, group_username)
            if add_result == 0:
                logger.info('auto invite %s to group' % username)
                self.send_msg_by_uid(u'邀请朋友加群，请进群改备注公司-职位-姓名哈，也可介绍自己，发个红包和大家熟悉一下~~', username)
            elif add_result == 1205:
                self.send_msg_by_uid(u'已经收到~可惜我这边拉人太频繁，被微信限制了呢,一个小时后会手动邀请您进相关群，请稍等~~', username)
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

    def schedule(self):
        if not self.schedule_remark:
            return
        if time.time() - self.remark_time > 36:
            while True:
                if len(self.contact_list) <= self.contact_index:
                    logger.info('contact index exceed')
                    break
                res = self.remark_contact(self.contact_list[self.contact_index])
                if res == 1 or res == 2 or res == 3:
                    self.contact_index = self.contact_index + 1
                    self.remark_time = time.time()
                    logger.info('set remark time run')
                    break
                else:
                    self.contact_index = self.contact_index + 1


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.schedule_remark = False
    bot.use_merge = bot.schedule_remark
    if not bot.auto_add_friend:
        bot.merge_group_names = [u'趣直播超级用户群', u'趣直播超级用户群2', u'趣直播超级用户群3', u'趣直播超级用户群4',
                                 u'趣直播超级用户群5', u'趣直播超级用户群6', u'趣直播超级用户群7']
    else:
        bot.merge_group_names = [u'趣直播超级用户群8', u'趣直播超级用户群9', u'趣直播超级用户群10', u'趣直播超级用户群11',
                                 u'深度学习DL大群', u'超级iOS群', u'超级iOS群2', u'超级iOS群3', u'互联网交流大群']
    bot.run()


if __name__ == '__main__':
    main()
