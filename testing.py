import imaplib
import email
from email.header import decode_header
import webbrowser
import os

username = 'ytscraper1@yandex.com'
password = '396ytscraper1!'

def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)

imap = imaplib.IMAP4_SSL("imap.yandex.com")

imap.login(username, password)