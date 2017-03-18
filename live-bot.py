#!/usr/bin/env python
# coding: utf-8
#

from wxbot import *


class MyWXBot(WXBot):
    def all_group_names(self):
        group_names = [u'趣直播超级用户群10', u'趣直播超级用户群9', u'趣直播超级用户群8', u'趣直播超级用户群7',
                       u'趣直播超级用户群6', u'趣直播超级用户群5', u'趣直播超级用户群4', u'趣直播超级用户群3',
                       u'趣直播超级用户群2', u'趣直播精华用户群', u'测试']
        # group_names = [u'测试']
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
                            print  '%s changed to %s' % (nickname, prefer_name)
                            time.sleep(10)
                            succeed_count = succeed_count + 1
                        elif remark_res == -1:
                            print 'exception'
                        elif remark_res == 1205:
                            print 'too frequent'
                            return
                        else:
                            print 'fail to change %s to %s code %d' % (nickname, prefer_name, remark_res)
                    else:
                        print 'fail change prefer name %s , nickname %s ' % (prefer_name, nickname)
                else:
                    pass
                    # print  'can not find prefer name %s'
            else:
                pass
                # print 'do not need change %s to %s' % (nickname, remark_name)
        print 'succeed count %d total %d' % (succeed_count, len(self.contact_list))

    def proc_msg1(self):
        self.batch_remark_names()

    def handle_msg_all(self, msg):
        # print json.dumps(msg)
        if msg['msg_type_id'] == 37:
            RecommendInfo = msg['content']['data']
            time.sleep(5)
            username = RecommendInfo['UserName']
            nickname = RecommendInfo['NickName']
            if not self.is_friend_in_any_group(username):
                self.apply_useradd_requests(RecommendInfo)
                print '[BOT] auto add user %s ' % (nickname)
                group_username = self.group_by_nickname(nickname)
                if (self.is_friend_in_group(username, group_username)):
                    print '[BOT] already in group skip %s' % (nickname)
                    time.sleep(5)
                    self.send_msg_by_uid(u'嗨 很高兴认识朋友~~我是趣直播创始人~~感谢朋友对趣直播的支持哈', username)
                else:
                    time.sleep(5)
                    add_result = self.add_friend_to_group(username, group_username)
                    if add_result:
                        time.sleep(5)
                        self.send_msg_by_uid(u'嗨 很高兴认识朋友，感谢朋友参加直播，这是我们知识直播平台的主播用户群 诚邀朋友加入~~进群改备注：公司-职位-姓名 '
                                             u'~~我是趣直播创始人，有问题随时联系哈~~~',
                                             username)
                    else:
                        time.sleep(5)
                        print '[ERROR] fail to add friend to group'
                        self.send_msg_by_uid(u'嗨 很高兴认识朋友~~我是趣直播创始人~~感谢朋友对趣直播的支持哈', username)
            else:
                print '[ERROR] already in group ignore %s ' % (nickname)
        elif msg['msg_type_id'] == 3:
            # self.send_remark_tip(msg)
            pass
        elif msg['msg_type_id'] == 12:
            self.batch_get_group_members()


            # def schedule(self):
            #     if len(self.contact_list) > 4000:
            #         self.bacth_remark_names()
            #     else:
            #         print 'contact list len %d' % len(self.contact_list)

    def group_by_nickname(self, nickname):
        default_group_name = u'趣直播超级用户群10'
        topic = self.userTopic(nickname)
        if topic is None:
            return default_group_name
        else:
            if topic['topicId'] == 1:
                return '趣直播后端用户群'
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
