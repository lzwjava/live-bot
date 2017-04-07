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
            self.send_msg_by_uid((u'嗨 很高兴认识%s朋友~~请转发朋友圈或者转发到相关行业群, 来加入深度学习大群, 并截图发过来哈~~大群里有大咖,同行们,名额有限,'
                                  u'感谢支持~~朋友圈也有一些直播回放,可观看哈~~'
                                  % (self.clean_nickname(nickname))),
                                 username)
        elif msg['msg_type_id'] == 4 or msg['msg_type_id'] == 99:
            # self.send_remark_tip(msg)
            username = msg['user']['id']
            nickname = msg['user']['name']
            content = msg['content']
            if content['type'] == 0:
                if content['data'].find(u'群') != -1:
                    self.send_msg_by_uid(u'请转发朋友圈或者转发到相关行业群, 来加入深度学习大群, '
                                         u'并截图发过来哈~~大群里有大咖,同行们,名额有限,感谢支持~~', username)
            elif content['type'] == 3:
                self.add_group(username, nickname)
        elif msg['msg_type_id'] == 12:
            pass
            # self.batch_get_group_members()
        elif msg['msg_type_id'] == 10000 and msg['user']['id'][:2] != '@@':
            if self.apply_failed:
                user_id = msg['user']['id']
                self.send_msg_by_uid((u'嗨 很高兴认识朋友~~请转发朋友圈或者转发到相关行业群, 来加入趣直播深度学习大群~~截图发过来哈~~大群里有大咖,同行们,名额有限,'
                                      u'感谢支持~~朋友圈也有一些直播回放,可观看哈'),
                                     user_id)
                logger.info('auto send msg 10000')
            else:
                logger.info('self applied not failed ignore')

    def add_group(self, username, nickname):
        group_username = u'深度学习DL大群'
        if (self.is_friend_in_group(username, group_username)):
            logger.info('already in group skip %s' % (nickname))
            self.send_msg_by_uid(u'朋友已经在群里啦 感谢', username)
        else:
            add_result = self.add_friend_to_group(username, group_username)
            if add_result:
                logger.info('auto invite %s to group' % nickname)
                self.send_msg_by_uid(u'请进群改备注公司-职位-姓名哈 也可发个红包和大家熟悉一下~~', username)
            else:
                logger.error('fail to add friend to group')
                self.send_msg_by_uid(u'感谢朋友支持 一会批量拉群哈', username)

    def ready(self):
        for group in self.group_list:
            logger.info(group['NickName'])


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.is_big_contact = False  # 如果确定通讯录过大，无法获取，可以直接配置，跳过检查。假如不是过大的话，这个方法可能无法获取所有的联系人
    bot.get_group_from_contact = False
    bot.run()


if __name__ == '__main__':
    main()
