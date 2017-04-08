#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *

logger = WXBot.init_logger()


class MyWXBot(WXBot):
    def handle_msg_all(self, msg):
        if msg['msg_type_id'] == 10000 and msg['user']['id'][:2] == '@@':
            group_id = msg['user']['id']
            self.update_member_count_by_id(group_id)

    def update_member_count_by_id(self, group_id):
        group = self.get_group_contact(group_id)
        nickname = group['NickName']
        member_count = len(group['MemberList'])
        self.update_member_count(nickname, member_count)

    def update_member_count(self, group_username, member_count):
        res = self.base_post_api_server('wechatGroups/update', {
            'groupUserName': group_username,
            'memberCount': member_count
        })
        if res['status'] == 'success':
            logger.info('update member count success')
        else:
            logger.error('update member count fail status %s' % res['status'])

    def ready(self):
        for group in self.group_list:
            group_username = group['UserName']
            logger.info(group['NickName'])
            self.update_member_count_by_id(group_username)


'''
    def schedule(self):
        self.send_msg(u'张三', u'测试')
        time.sleep(1)
'''


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.run()


if __name__ == '__main__':
    main()
