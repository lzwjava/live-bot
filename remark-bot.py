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
            if 'RemarkName' not in contact or not contact['RemarkName']:
                prefer_name = self.get_prefer_username(uid)
                if prefer_name is not None:
                    if nickname == prefer_name:
                        logger.info('%s name equal skip', nickname)
                    elif 'span' not in prefer_name:
                        # rate: 1 min 10, 1 hour 100
                        remark_res = self.set_remarkname(uid, prefer_name)
                        if remark_res == 0:
                            logger.info('%s changed to %s' % (nickname, prefer_name))
                            time.sleep(10)
                            self.send_msg_by_uid(u'%s 备注为 %s' % (nickname, prefer_name))
                            succeed_count = succeed_count + 1
                        elif remark_res == -1:
                            print 'exception'
                        elif remark_res == 1205:
                            logger.info('too frequent %d' % (succeed_count))
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
    bot.run()


if __name__ == '__main__':
    main()
