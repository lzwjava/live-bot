#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *


class MyWXBot(WXBot):
    def in_live_groups(self, target_group_name):
        group_names = [u'测试']
        for group_name in group_names:
            if group_name == target_group_name:
                return True
        return False

    def handle_msg_all(self, msg):
        print json.dumps(msg)
        if msg['msg_type_id'] == 37:
            RecommendInfo = msg['content']['data']
            time.sleep(5)
            self.apply_useradd_requests(RecommendInfo)
            nickname = RecommendInfo['NickName']
            print '[BOT] auto add user %s ' % (nickname)
            username = RecommendInfo['UserName']
            group_username = u'趣直播超级用户群10'
            if (self.is_friend_in_group(username, group_username)):
                print '[BOT] already in group skip %s' % (nickname)
                time.sleep(5)
                self.send_msg_by_uid(u'嗨 很高兴认识朋友~~我是趣直播创始人~~感谢朋友对趣直播的支持哈', username)
            else:
                time.sleep(5)
                add_result = self.add_friend_to_group(username, group_username)
                if add_result:
                    time.sleep(5)
                    self.send_msg_by_uid(u'嗨 很高兴认识朋友，这是我们知识直播平台的主播用户群 诚邀朋友加入~~进群改备注：公司-职位-姓名 '
                                         u'~~我是趣直播创始人，有问题随时联系哈~~~',
                                         username)
                else:
                    time.sleep(5)
                    print '[ERROR] fail to add friend to group'
                    self.send_msg_by_uid(u'嗨 很高兴认识朋友~~我是趣直播创始人~~感谢朋友对趣直播的支持哈', username)
        elif msg['msg_type_id'] == 3:
            group_name = msg['user']['name']
            group_id = msg['user']['id']
            if self.in_live_groups(group_name):
                send_username = msg['content']['user']['name']
                send_id = msg['content']['user']['id']
                if "-" not in send_username:
                    self.batch_get_group_members()
                    update_name = self.get_group_member_prefer_name(self.get_group_member_name(group_id, send_id))
                    if update_name is not None and "-" not in update_name:
                        self.send_msg_by_uid('楼上请按格式改备注(公司-职位-姓名)哈', group_id)


'''
    def schedule(self):
        self.send_msg(u'张三', u'测试')
        time.sleep(1)
'''


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.is_big_contact = False  # 如果确定通讯录过大，无法获取，可以直接配置，跳过检查。假如不是过大的话，这个方法可能无法获取所有的联系人
    bot.run()


if __name__ == '__main__':
    main()
