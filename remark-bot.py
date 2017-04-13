#!/usr/bin/env python
# coding: utf-8
#


from wxbot import *

logger = WXBot.init_logger()


class MyWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)

    def handle_msg_all(self, msg):
        pass

    def batch_remark_names(self):
        succeed_count = 0
        for contact in self.contact_list:
            ok = self.remark_contact(contact)
            if ok == 1:
                succeed_count = succeed_count + 1
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
