# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe.utils.password import get_decrypted_password

__version__ = '0.0.1'
#
# @frappe.whitelist(allow_guest=True)
# def authenticate(doc, user, password):
#     print "Datos ", user, password
#
#     user = frappe.db.get_value("User", {'user':user, 'password':password})
#     print "User ", user
#     c = False
#     a = doc.posting_date
#     print "User format", user.formato
#     if user:
#         flag = '1'
#         flag_c = '0'
#         flag_a = '0'
#         c = user.formato
#         a = user.date_active
#     else:
#         flag = '0'
#         flag_c = '0'
#         flag_a = '0'
#
#     if c == True:
#         flag_c = '1'
#     else:
#         flag_c = '0'
#
#     if a:
#         date= datetime.now()
#         limit= (date-a).days
#         if limit > 5:
#             flag_a = '1'
#         else:
#             flag_a = '0'
#
#     print "User ", user
#
#     return flag, flag_c, flag_a
