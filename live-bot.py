#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *
import logging
import os
from sys import platform
import redis

if platform == "linux" or platform == "linux2":
    is_linux = True
else:
    is_linux = False

if not is_linux:
    logger_path = '/Users/lzw/Downloads/myapp.log'
else:
    logger_path = '/root/bot.log'

logger = logging.getLogger('wxbot')
hdlr = logging.FileHandler(logger_path)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)


class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)
        self.redis_obj = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.add_count = 0

    def all_group_names(self):
        group_names = [u'趣直播超级用户群11', u'趣直播超级用户群10', u'趣直播超级用户群9', u'趣直播超级用户群8', u'趣直播超级用户群7',
                       u'趣直播超级用户群6', u'趣直播超级用户群5', u'趣直播超级用户群4', u'趣直播超级用户群3',
                       u'趣直播超级用户群2', u'趣直播超级用户群1', u'测试']
        return group_names

    def in_live_groups(self, target_group_name):
        for group_name in self.all_group_names():
            if group_name == target_group_name:
                return True
        return False

    def is_friend_in_any_group(self, uid):
        for group_name in self.all_group_names():
            if self.is_friend_in_group(uid, group_name):
                return True
        return False

    def send_remark_tip(self, msg):
        group_name = msg['user']['name']
        group_id = msg['user']['id']
        if self.in_live_groups(group_name):
            send_username = msg['content']['user']['name']
            send_id = msg['content']['user']['id']
            if "-" not in send_username:
                self.batch_get_group_members()
                update_name = self.get_group_member_prefer_name(self.get_group_member_name(group_id, send_id))
                if update_name is not None and "-" not in update_name:
                    self.send_msg_by_uid(u'@%s 请按格式改备注(公司-职位-姓名)哈' % update_name, group_id)

    def get_prefer_username(self, uid):
        for group in self.group_list:
            group_nickname = group['NickName']
            group_id = group['UserName']
            if self.is_friend_in_group(uid, group_nickname):
                name = self.get_group_member_name(group_id, uid)
                if name is None:
                    pass
                else:
                    if 'display_name' in name:
                        return name['display_name']
                    else:
                        pass
        return None

    def batch_remark_names(self):
        succeed_count = 0
        for contact in self.contact_list:
            uid = contact['UserName']
            nickname = contact['NickName']
            remark_name = contact['RemarkName']
            if not remark_name:
                prefer_name = self.get_prefer_username(uid)
                if prefer_name is not None:
                    if 'span' not in prefer_name and nickname != prefer_name:
                        remark_res = self.set_remarkname(uid, prefer_name)
                        if remark_res == 0:
                            logger.info('%s changed to %s' % (nickname, prefer_name))
                            time.sleep(10)
                            succeed_count = succeed_count + 1
                        elif remark_res == -1:
                            print 'exception'
                        elif remark_res == 1205:
                            logger.info('too frequent ' % (succeed_count))
                            return
                        else:
                            logger.info('fail to change %s to %s code %d' % (nickname, prefer_name, remark_res))
                    else:
                        logger.info('fail change prefer name %s , nickname %s ' % (prefer_name, nickname))
                else:
                    pass
                    # print  'can not find prefer name %s'
            else:
                prefer_name = self.get_prefer_username(uid)
                if prefer_name is not None:
                    if remark_name != prefer_name:
                        pass
                        # print 'remark name %s prefer name %s' % (remark_name, prefer_name)
                        # print 'do not need change %s to %s' % (nickname, remark_name)

        logger.info('succeed count %d total %d' % (succeed_count, len(self.contact_list)))

    def proc_msg1(self):
        for group in self.group_list:
            group_nickname = group['NickName']
            print group_nickname
        self.batch_remark_names()

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
            time.sleep(5)
            username = RecommendInfo['UserName']
            nickname = RecommendInfo['NickName']
            apply_res = self.apply_useradd_requests(RecommendInfo)
            if not apply_res:
                logger.error('apply failed %s' % (nickname))
                self.save_recommend_info(username, RecommendInfo)
                return
            self.add_count = self.add_count + 1
            logger.info('auto add user %s count: %d' % (nickname, self.add_count))
            group_username = u'趣直播超级用户群11'
            if (self.is_friend_in_group(username, group_username)):
                logger.info('already in group skip %s' % (nickname))
                time.sleep(5)
                self.send_msg_by_uid(u'嗨 很高兴认识朋友~~我是趣直播创始人~~感谢朋友对趣直播的支持~请问朋友哪里高就?~~多交流或合作哈', username)
            else:
                time.sleep(5)
                add_result = self.add_friend_to_group(username, group_username)
                if add_result:
                    time.sleep(5)
                    logger.info('auto invite %s to group' % nickname)
                    self.send_msg_by_uid((u'嗨 很高兴认识%s朋友 感谢参加直播或者看到趣直播的融资报道，感谢支持~~'
                                          u'我是趣直播创始人，朋友圈也有趣直播介绍，有问题随时联系~~朋友在哪里高就？想多多了解朋友哈~~ '
                                          u'这里有个我们知识直播平台的主播用户群，有BAT大咖，群里每天还有红包~~也可加下哈~~~进群改备注：公司-职位-姓名~~~'
                                          % (self.clean_nickname(nickname))),
                                         username)
                else:
                    time.sleep(5)
                    self.save_group_recommend_info(username, RecommendInfo)
                    logger.error('fail to add friend to group')
                    self.send_msg_by_uid(u'嗨 很高兴认识朋友~~我是趣直播创始人~~感谢朋友对趣直播的支持~~请问朋友哪里高就?想了解了解朋友哈', username)
        elif msg['msg_type_id'] == 3:
            # self.send_remark_tip(msg)
            pass
        elif msg['msg_type_id'] == 12:
            pass
            # self.batch_get_group_members()


            # def schedule(self):
            #     if len(self.contact_list) > 4000:
            #         self.bacth_remark_names()
            #     else:
            #         print 'contact list len %d' % len(self.contact_list)

    def group_by_nickname(self, nickname):
        default_group_name = u'趣直播超级用户群11'
        topic = self.userTopic(nickname)
        if topic is None:
            return default_group_name
        else:
            if topic['topicId'] == 1:
                return default_group_name
            else:
                return default_group_name

    def userTopic(self, username):
        url = 'https://api.quzhiboapp.com/users/userTopic'
        params = {
            'username': username
        }
        r = self.session.get(url, params=params)
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        if dic['status'] == 'success':
            return dic['result']
        else:
            print 'not find topic status: %s' % (dic['status'])
            return None


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.is_big_contact = False  # 如果确定通讯录过大，无法获取，可以直接配置，跳过检查。假如不是过大的话，这个方法可能无法获取所有的联系人
    bot.run()


if __name__ == '__main__':
    main()
