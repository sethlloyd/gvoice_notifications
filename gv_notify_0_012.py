#! /usr/bin/env python

from googlevoice import Voice
import xmpp
from BeautifulSoup import BeautifulSoup
import time
import getpass
import smtplib






voice = Voice()
g_user = raw_input("Complete google voice login name: ")
g_passwd = getpass.getpass("Google voice password: ")
voice.login(g_user, g_passwd)


EMAIL_NOTI = False

# determine if user wants im or email notification
if raw_input("Enter 0 for email notification, anything else for IM: ")=='0':
    EMAIL_NOTI = True
    

# The following assumes that the account to send the message from is a gmail.com based account
# Obviously, if this is not true, the parameters would need to be changed

if EMAIL_NOTI:
    email={}
    email['Server'] = "smtp.gmail.com"
    email['From'] = g_user
    email['To'] = "%s" % raw_input("Email address to send to: ")
    
else:
    im_username = raw_input("Jabber account user name to send message from (for gmail do not include @gmail.com): ")
    im_passwd = getpass.getpass("Jabber account password: ")
    im_sendto = raw_input("Account to send message to (for gmail, INCLUDE @gmail.com): ")
    client = xmpp.Client('gmail.com',debug=[])
    client.connect(server=('talk.google.com',5223))
    client.auth(im_username,im_passwd, 'botty')
    client.sendInitPresence()


first = True
sms_count = {}

# repeat the following loop until the program is killed
while True:
    # first find out how many unread messages there are

    allsms = voice.sms()
    new_sms = allsms['unreadCounts']['sms']
    smss = allsms['messages']
    found = 0


    # iterate through unread sms messages, keeping track of what notifications have been sent.
    # it's a bit tricky to keep track of what's really new since
    # an unread sms thread may contain more than 1 new message since the last iteration, though google
    # voice only reports one unread message (i.e. just that there are new messages in that thread)
    # thus for each thread you have, this keeps track of how many messages there were at
    # the previous iteration and notifies you of all new messages since
    if first:
        sms_parse = BeautifulSoup(voice.sms_html())
    else:
        if new_sms>0:
            sms_parse = BeautifulSoup(voice.sms_html())
            
    
    for itms in reversed(smss.keys()):

        # the first time we want to build the list of message totals
        if first:
            found=-1
            
        if found == new_sms:
            break

        smsID=smss[itms]['id']


        # BeautifulSoup very nicely parses the html tags to pull out the actual text messages
        sms_content=sms_parse.find(id=smsID).findAll(attrs={"class":"gc-message-sms-text"})
        sms_from=sms_parse.find(id=smsID).findAll(attrs={"class":"gc-message-sms-from"})

        # here's the actual number of texts you've received from the specific user
        clen=len(sms_content)

        # check if we already have an entry for that sender, and compare with the number of previous
        # messages received to see how many are actually new.  The first time the script runs, it
        # will only send you notification of the last received sms for any sms messages marked as unread
        
        if smsID in sms_count:
            unread_sms=clen-sms_count[smsID]            
        else:
            if first:              
                unread_sms=1
            else:
                unread_sms=clen
                

        # store the unread count for comparison next time
        sms_count[smsID]=clen

        # build up the notification message containing all new sms messages
        if smss[itms]['isRead']== False:

            if (unread_sms > 0) and (first == False):

                if EMAIL_NOTI:
                    email['Subject'] = "SMS from " + sms_from[clen-1].string[4:-4]
                    email['Text']=""

                    for i in range(clen-unread_sms,clen):
                        if ("Me:" in sms_from[i].string) == False:
                            email['Text'] = email['Text'] + sms_content[i].string + '\r\n'

                    server = smtplib.SMTP(email['Server'], 587)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(g_user, g_passwd)
                    server.sendmail(g_user,email['To'],("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (email['From'],email['To'],email['Subject'],email['Text'])))
                    server.quit()


                else:
                    im="SMS from " + sms_from[clen-1].string[4:-2]                

                    for i in range(clen-unread_sms,clen):
                        if ("Me:" in sms_from[i].string) == False:
                            im=im + sms_content[i].string + '\r\n'

                    message= xmpp.Message(im_sendto,im)
                    message.setAttr('type','chat')
                    client.send(message)

            found=found+1

    first= False

    #sleep for 60 seconds before repeating.
    time.sleep(60)
