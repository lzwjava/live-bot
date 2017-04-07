#!/usr/bin/env python
# coding: utf-8
#


from wxbot import *

logger = WXBot.init_logger()


class MyWXBot(WXBot):
    def handle_msg_all(self, msg):
        pass

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

    def ready(self):
        for group in self.group_list:
            group_nickname = group['NickName']
            logger.info(group_nickname)
        self.batch_remark_names()


def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'
    bot.is_big_contact = False  # 如果确定通讯录过大，无法获取，可以直接配置，跳过检查。假如不是过大的话，这个方法可能无法获取所有的联系人
    bot.get_group_from_contact = False
    bot.run()


if __name__ == '__main__':
    main()
