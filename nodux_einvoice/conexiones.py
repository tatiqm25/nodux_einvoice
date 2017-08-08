#! -*- coding: utf8 -*-
from __future__ import unicode_literals
import frappe
import json
import copy
from frappe import throw, _
from frappe.utils.password import get_decrypted_password
from frappe.utils import flt, cint
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import msgprint, _
import base64
import StringIO
from lxml import etree
from lxml.etree import DocumentInvalid
import xml.etree.cElementTree as ET
import time
#libreria para codigo de barras
#import code128
import xml.etree.ElementTree
import xmlrpclib
import shutil
import os.path
import unicodedata
import re
from datetime import datetime
from frappe.utils.password import get_decrypted_password
#validacion de email
#from validate_email import validate_email
import commands
import logging
import smtplib, os
import string
import base64
#import psycopg2
from SimpleXMLRPCServer import SimpleXMLRPCServer
import hashlib
import datetime
import subprocess
import random
from pytz import timezone
#import pystmark
from lxml.etree import DocumentInvalid
try:
    from OpenSSL import crypto
except ImportError:
    raise ImportError('Instalar la libreria para soporte OpenSSL: pip install PyOpenSSL')
try:
    from ctypes import *
except ImportError:
    raise ImportError('Libreria CTypes no esta disponible')
try:
    from suds.client import Client
    from suds.transport import TransportError
except ImportError:
    raise ImportError('Instalar Libreria suds')
import utils
import xmlrpclib

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

def is_even(n):
    return n % 2 == 0

server = SimpleXMLRPCServer(("192.168.1.43", 8000))
server.register_function(is_even, "is_even")
server.serve_forever()


SCHEMAS = {
    'out_invoice': 'schemas/factura.xsd',
    'out_credit_note': 'schemas/notaCredito.xsd',
    'in_withholding': 'schemas/comprobanteRetencion.xsd',
    'out_debit_note': 'schemas/notaDebito.xsd',
    'out_shipment' : 'schemas/guiaRemision.xsd',
    'lote':'schemas/lote.xsd'
}

#NUEVA_RUTA = '/var/www/vhosts/nodux.ec/.noduxenvs/nodux34auth'
NUEVA_RUTA = '/home/frappe/frappe_auth'

@frappe.whitelist(allow_guest=True)
def replace_character(doc, cadena):
        reemplazo = {u"Â":"A", u"Á":"A", u"À":"A", u"Ä":"A", u"É":"E", u"È":"E", u"Ê":"E",u"Ë":"E",
            u"Í":"I",u"Ì":"I",u"Î":"I",u"Ï":"I",u"Ó":"O",u"Ò":"O",u"Ö":"O",u"Ô":"O",u"Ú":"U",u"Ù":"U",u"Ü":"U",
            u"Û":"U",u"á":"a",u"à":"a",u"â":"a",u"ä":"a",u"é":"e",u"è":"e",u"ê":"e",u"ë":"e",u"í":"i",u"ì":"i",
            u"ï":"i",u"î":"i",u"ó":"o",u"ò":"o",u"ô":"o",u"ö":"o",u"ú":"u",u"ù":"u",u"ü":"u",u"û":"u",u"ñ":"n",
            u"Ñ":"N", u"Nº":"No", u"nº":"No"}
        regex = re.compile("(%s)" % "|".join(map(re.escape, reemplazo.keys())))
        nueva_cadena = regex.sub(lambda x: str(reemplazo[x.string[x.start():x.end()]]), cadena)
        return nueva_cadena

@frappe.whitelist(allow_guest=True)
def replace_character_html(doc, cadena):
    reemplazo = {u"Á":"&Aacute;", u"É":"&Eacute;",
        u"Í":"&Iacute;",u"Ó":"&Oacute;",u"Ú":"&Uacute;",u"á":"&aacute;",u"é":"&eacute;",
        u"í":"&iacute;",u"ó":"&oacute;",u"ú":"&uacute;", u"ñ":"&nacute;", u"Ñ":"&Nacute;"}
    regex = re.compile("(%s)" % "|".join(map(re.escape, reemplazo.keys())))
    nueva_cadena = regex.sub(lambda x: str(reemplazo[x.string[x.start():x.end()]]), cadena)
    return nueva_cadena

@frappe.whitelist(allow_guest=True)
def authenticate(user, password):
    print "Esta ingresando aqui datos"
    user = frappe.db.get_value("User", {'user':user, 'password':password})
    c = False
    a = doc.posting_date

    if user:
        flag = '1'
        flag_c = '0'
        flag_a = '0'
        for u in user:
            c = u.formato
            a = u.date_active
    else:
        flag = '0'
        flag_c = '0'
        flag_a = '0'

    if c == True:
        flag_c = '1'
    else:
        flag_c = '0'

    if a:
        date= datetime.now()
        limit= (date-a).days
        if limit > 5:
            flag_a = '1'
        else:
            flag_a = '0'

    return flag, flag_c, flag_a

@frappe.whitelist(allow_guest=True)
def save_pk12(doc, empresa):
    nuevaruta = NUEVA_RUTA + '/certificados'
    if not os.path.exists(nuevaruta):
        os.makedirs(nuevaruta)
    return nuevaruta

@frappe.whitelist(allow_guest=True)
def path_files(doc, ruc):
    nuevaruta = NUEVA_RUTA + '/comprobantes/'
    return nuevaruta

@frappe.whitelist(allow_guest=True)
def validate_xml(doc, document, type_document):
    schema = SCHEMAS[type_document]
    message_invalid = u"El sistema generó el XML pero el comprobante electrónico no pasa el formato. Revise los campos de su factura"
    file_path = os.path.join(os.path.dirname(__file__), schema)
    schema_file = open(file_path, 'r')
    xmlschema_doc = etree.parse(schema_file)
    xmlschema = etree.XMLSchema(xmlschema_doc)
    document= etree.fromstring(document)
    try:
        xmlschema.assertValid(document)
    except DocumentInvalid as e:
        print e
        print ('Error de Datos', message_invalid)
        return (message_invalid+str(e))

@frappe.whitelist(allow_guest=True)
def check_digital_signature(doc, file_pk12):
    error = '0'
    if os.path.exists(file_pk12):
        pass
    else:
        error = '1'
    return error

@frappe.whitelist(allow_guest=True)
def apply_digital_signature(doc, xml_document, file_pk12, password):
    xml_document = cls.replace_character(xml_document)
    firma_path = os.path.join(os.path.dirname(__file__), 'firma/firmaXadesBes.jar')
    p = subprocess.Popen(['java', '-jar', firma_path, xml_document, file_pk12, password], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = p.communicate()
    print res
    return res[0]

@frappe.whitelist(allow_guest=True)
def send_receipt(doc, document):
    buf = StringIO.StringIO()
    buf.write(document)
    buffer_xml = base64.encodestring(buf.getvalue())
    if not utils.check_service('prueba'):
        print ('Error SRI', 'Servicio SRI no disponible.')

    client = Client(SriService.get_active_ws()[0])
    result =  client.service.validarComprobante(buffer_xml)
    print "result", result

    if result[0] == 'RECIBIDA':
        return True
    else:
        for m in result[1][0][0][1][0]:
            if m.identificador == '43':
                return True
            else:
                response = u'Comprobante Electrónico DEVUELTO:\nError : ' +str(m.mensaje) + '\nIdentificador : ' +str(m.identificador) + '\nTipo : ' +str(m.tipo)
                return response

@frappe.whitelist(allow_guest=True)
def request_authorization(doc, access_key, empresa, tipo_comprobante, documento):
    messages = []
    m = ""
    client = Client(SriService.get_active_ws()[1])
    result =  client.service.autorizacionComprobante(access_key)
    print "El resultado es ", result
    ruta_actual = os.path.join(os.path.dirname(__file__))
    ahora = datetime.datetime.now()
    year = str(ahora.year)
    if ahora.month < 10:
        month = '0'+ str(ahora.month)
    else:
        month = str(ahora.month)
    if tipo_comprobante == 'out_invoice':
        tipo = 'fact_'
    if tipo_comprobante == 'in_withholding':
        tipo = 'c_r'
    if tipo_comprobante == 'out_credit_note':
        tipo = 'n_c'
    if tipo_comprobante == 'out_debit_note':
        tipo = 'n_d'
    if tipo_comprobante == 'out_shipment':
        tipo = 'g_r'
    nuevaruta = NUEVA_RUTA + '/comprobantes/'+empresa+'/'+year+'/'+month
    if result.autorizaciones:
        autorizacion = result.autorizaciones[0][0]
        if autorizacion.estado == 'AUTORIZADO':
            num = str(autorizacion.numeroAutorizacion)
            ruc = num[10:23]
            est = num[24:27]
            emi= num[27:30]
            sec = num[30:39]
            numero = ruc+'_'+est+'-'+emi+'-'+sec
            ruta_db = os.getcwd()+'/comprobantes/'+empresa+'/'+ year+'/'+month +'/'+tipo+numero
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado_sri').text = autorizacion.estado
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = autorizacion.numeroAutorizacion
            #etree.SubElement(autorizacion_xml, 'ambiente').text = 'PRODUCCION'
            etree.SubElement(autorizacion_xml, 'ambiente').text = 'PRUEBAS' #autorizacion.ambiente.replace("Ó","O") #Nodux autorizacion.ambiente
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(autorizacion.comprobante)
            autorizacion_xml = etree.tostring(autorizacion_xml, encoding = 'utf8', method = 'xml')
            messages=" ".join(messages)
            auth = autorizacion.estado
            if not os.path.exists(nuevaruta):
                os.makedirs(nuevaruta)
            return autorizacion_xml, False, 'AUTORIZADO' , ruta_db, numero, num
        else:
            identificador = result.autorizaciones[0][0].mensajes[0][0].identificador#cls.replace_character(str(result.autorizaciones[0][0].mensajes[0][0].identificador))
            mensaje = result.autorizaciones[0][0].mensajes[0][0].mensaje#cls.replace_character(str(result.autorizaciones[0][0].mensajes[0][0].mensaje))
            informacion = result.autorizaciones[0][0].mensajes[0][0].informacionAdicional#cls.replace_character(str(result.autorizaciones[0][0].mensajes[0][0].informacionAdicional))
            tipo = result.autorizaciones[0][0].mensajes[0][0].tipo#cls.replace_character(str(result.autorizaciones[0][0].mensajes[0][0].tipo))
            mensaje = 'Tipo: '+tipo+'\nIdentificador: '+identificador +'\nMensaje: '+ mensaje +'\nInformacion Adicional: '+  informacion
            num = str(access_key)
            ruc = num[10:23]
            est = num[24:27]
            emi= num[27:30]
            sec = num[30:39]
            numero = ruc+'_'+est+'-'+emi+'-'+sec
            ruta_db = os.getcwd()+'/comprobantes/'+empresa+'/'+ year+'/'+month +'/'+tipo+numero
            autorizacion_xml = etree.Element('autorizacion')
            etree.SubElement(autorizacion_xml, 'estado_sri').text = 'NO AUTORIZADO'
            etree.SubElement(autorizacion_xml, 'numeroAutorizacion').text = num
            #etree.SubElement(autorizacion_xml, 'ambiente').text = 'PRODUCCION'
            etree.SubElement(autorizacion_xml, 'ambiente').text = 'PRUEBAS' #autorizacion.ambiente.replace("Ó","O") #Nodux autorizacion.ambiente
            etree.SubElement(autorizacion_xml, 'comprobante').text = etree.CDATA(documento)
            autorizacion_xml = etree.tostring(autorizacion_xml, encoding = 'utf8', method = 'xml')
            return mensaje, False, 'NO AUTORIZADO' , ruta_db, numero, num

@frappe.whitelist(allow_guest=True)
def prueba():
    print "Establece conexiones"

@frappe.whitelist(allow_guest=True)
def connect_db(doc, nombre, cedula, ruc, nombre_e, tipo, fecha, empresa, numero, path_xml, path_pdf,estado, auth, email, email_e, total):
    config = {
        'url': 'http://192.168.1.45/xmlrpc.php',
        'username': 'tatiana',
        'password': 'tatiana12354',
    }
    server = xmlrpclib.ServerProxy(config['url'], allow_none=True);
    #print server.system.listMethods() # si podemos listar las operaciones del servicio web, hemos conectado al servidor
    result= server.wp.save_user(cedula, email, nombre)
    result_invoice= server.wp.save_invoice(cedula, ruc, tipo, fecha, empresa, numero, auth, total, path_xml, path_pdf)
    print result, result_invoice

@frappe.whitelist(allow_guest=True)
def send_mail(cls, name_pdf, name, p_xml, p_pdf, from_email, to_email, n_tipo, num_fac, client, empresa_, ruc):
    pool =Pool()
    Company = pool.get('company.company')
    Party = pool.get('party.party')

    companys = Company.search([('id', '!=', None)])
    parties = Party.search([('vat_number', '=', ruc)])

    correos = Pool().get('party.contact_mechanism')
    correo = correos.search([('type','=','email')])
    for c in companys:
        company = c
    if company:
        servidor = company.servidor
        puerto = company.puerto
        API_KEY = company.password

    for p in parties:
        party = p

    if party.formato == True:
        color = "#" + party.color
        logo = party.nombre_logo
        msm_cuerpo = party.msm_cuerpo

        ruta_logo = 'http://nodux.ec:8085/static/img/empresaslogos/'+str(logo)
        html = """\
                <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
                <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <title>Comprobantes Electr&oacute;nicos</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                </head>
                <body style="margin: 0; padding: 10;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                <td>
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="600">
                <tr>
                <td align="center" bgcolor={color} style="color: #ffffff; font-family: Verdana, sans-serif; font-size: 20px; padding: 40px 0 30px 0; border-radius: 5px;"><img src={ruta_logo} alt={empresa_}>
                </td>
                </tr>
                <tr>
                <td bgcolor="#ffffff" style="padding: 40px 30px 40px 30px;">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                     <tr>
                    <td style="color: #153643; font-family: Arial, sans-serif; font-size: 14px;">
                    <b> Estimado(a) {client} :</b>
                    <p>
                    </td>
                     </tr>
                     <tr>
                    <td style="color: #153643; font-family: Arial, sans-serif; font-size: 14px; line-height: 20px;">
                    <p>
                    {empresa_} {msm_cuerpo}: {n_tipo} {num_fac}, el cual est&aacute; disponible para su visualizaci&oacute;n y descarga.
                    <p>
                      Para consultar sus comprobantes electr&oacute;nicos dir&iacute;jase a:  <a href= "http://comprobantes.nodux.ec/" style="color: #C61F34;">comprobantes.nodux.ec</a>. No olvide ingresar como usuario y contraseña  su número de identificaci&oacute;n (c&eacute;dula o RUC)
                    </td>
                    </tr>
                    <tr>
                    <td style="padding: 20px 0 10px 0; color: #153643; font-family: Arial, sans-serif; font-size: 12px; line-height: 20px;">
                     <b>Recuerde: </b> La representaci&oacute;n impresa del comprobante electr&oacute;nico es el archivo PDF adjunto. Posee validez tributaria y podr&aacute; imprimirlo solamente en los casos que el SRI lo dispone.
                    </td>
                    </tr>
                    <tr>
                    <td bgcolor="#ffffff" style="padding: 20px 30px 0px 30px;">
                    <center><img src="http://nodux.ec:8085/static/img/logo-email.png" alt="NODUX C&iacute;a. Ltda.">
                    </center>
                    </td>
                    </tr>
                    </table>
                    </td>
                    </tr>
                     <tr>
                     <td bgcolor={color} style="padding: 30px 30px 30px 30px; color: #153643; font-family: Arial, sans-serif; font-size:13px; line-height: 20px; border-radius: 5px">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                     <tr>
                    <td style="color: #ffffff; font-family: Arial, sans-serif; font-size: 14px;">
                     &reg; Nodux. C&iacute;a. Ltda. 2016<br/>
                    </td>
                    <td>
                     <td align="right" width "25%" style="color: #153643; font-family: Arial, sans-serif; font-size: 13px; line-height: 20px;">
                     <table border="0" cellpadding="0" cellspacing="0">
                    <tr>
                    <td style="color: #ffffff; font-family: Arial, sans-serif; font-size: 13px; line-height: 20px;">
                     <a href="https://twitter.com/noduxEC"> Twitter
                     </a>
                    </td>
                    <td style="font-size: 0; line-height: 0;" width="20">&nbsp;</td>
                    <td>
                     <a href="https://www.facebook.com/nodux"> Facebook
                     </a>
                    </td>
                   </tr>
                    </table>
                   </td>
                   </td>
                   </tr>
                   </table>
                   </td>
                   </tr>
                    </table>
                    </td>
                    </tr>
                    </table>
                 </body>
                 </html>
                      """.format(ruta_logo=ruta_logo, color= color, msm_cuerpo= msm_cuerpo, client=client, empresa_=empresa_, n_tipo=n_tipo, num_fac=num_fac)
    else:
            html = """\
                    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
                    <html xmlns="http://www.w3.org/1999/xhtml">
                     <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                    <title>Comprobantes Electr&oacute;nicos</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    </head>
                    <body style="margin: 0; padding: 10;">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                     <td>
                    <table align="center" border="0" cellpadding="0" cellspacing="0" width="600">
                     <tr>
                    <td align="center" bgcolor="#C61F34" style="color: #ffffff; font-family: Verdana, sans-serif; font-size: 20px; padding: 40px 0 30px 0; border-radius: 5px;"><img src="http://nodux.ec:8085/static/img/logo-comprobantes.png" alt="NODUX C&iacute;a. Ltda.">
                    <p>
                    El sistema experto en gesti&oacute;n empresarial
                    </td>
                     </tr>
                     <tr>
                    <td bgcolor="#ffffff" style="padding: 40px 30px 40px 30px;">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                     <tr>
                    <td style="color: #153643; font-family: Arial, sans-serif; font-size: 14px;">
                    <b> Estimado(a) {client} :</b>
                    <p>
                    </td>
                     </tr>
                     <tr>
                    <td style="color: #153643; font-family: Arial, sans-serif; font-size: 14px; line-height: 20px;">
                    <p>
                    Nodux le informa que {empresa_} le ha emitido un comprobante electr&oacute;nico: {n_tipo} {num_fac}, el cual est$aacute; disponible para su visualizaci&oacute;n y descarga.
                    <p>
                      Para consultar sus comprobantes electr&oacute;nicos dir&iacute;jase a:  <a href= "http://comprobantes.nodux.ec/" style="color: #C61F34;">comprobantes.nodux.ec</a>. No olvide ingresar como usuario y contraseña  su n&uacute;mero de identificaci&oacute;n (c&eacute;dula o RUC)
                    </td>
                     </tr>
                     <tr>
                    <td style="padding: 20px 0 30px 0; color: #153643; font-family: Arial, sans-serif; font-size: 12px; line-height: 20px;">
                     <b>Recuerde: </b> La representaci&oacute;n impresa del comprobante electr&oacute;nico es el archivo PDF adjunto. Posee validez tributaria y podr&aacute; imprimirlo solamente en los casos que el SRI lo dispone.
                    </td>
                     </tr>
                    </table>
                    </td>
                     </tr>
                     <tr>
                     <td bgcolor="#C61F34" style="padding: 30px 30px 30px 30px; color: #153643; font-family: Arial, sans-serif; font-size:13px; line-height: 20px; border-radius: 5px">
                     <table border="0" cellpadding="0" cellspacing="0" width="100%">
                     <tr>
                    <td style="color: #ffffff; font-family: Arial, sans-serif; font-size: 14px;">
                     &reg; Nodux. C&iacute;a. Ltda. 2016<br/>
                    </td>
                    <td>
                     <td align="right" width "25%" style="color: #153643; font-family: Arial, sans-serif; font-size: 13px; line-height: 20px;">
                     <table border="0" cellpadding="0" cellspacing="0">
                    <tr>
                     <td style="color: #ffffff; font-family: Arial, sans-serif; font-size: 13px; line-height: 20px;">
                      <a href="https://twitter.com/noduxEC"> Twitter
                      </a>
                     </td>
                     <td style="font-size: 0; line-height: 0;" width="20">&nbsp;</td>
                     <td>
                      <a href="https://www.facebook.com/nodux"> Facebook
                      </a>
                     </td>
                    </tr>
                     </table>
                    </td>
                    </td>
                     </tr>
                    </table>
                    </td>
                     </tr>
                    </table>
                     </td>
                    </tr>
                     </table>
                    </body>
                    </html>
                    """.format(client=client, empresa_=empresa_, n_tipo=n_tipo, num_fac=num_fac)

    for mail in correo:
        if mail.party == company.party:
            SENDER = mail.value


    toaddr= to_email
    msg = MIMEMultipart()
    msg['From'] = 'etqm25@gmail.com'
    msg['To'] = 'etquizhpem@unl.edu.ec'
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = n_tipo + ' '+num_fac

    client = client.upper()
    """
    if (client == "CONSUMIDOR FINAL") | (from_email == toaddr):
        pass
    else:

        message = pystmark.Message(sender=SENDER, to=toaddr, subject=n_tipo + ' '+num_fac,
        html=html)

        filename = p_xml
        with open(filename) as f:
            message.attach_binary(f.read(), filename)
        filename = p_pdf
        with open(filename) as f:
            message.attach_binary(f.read(), filename)
        pystmark.send(message, api_key=API_KEY)

        pass
    """
    # pdf = MIMEApplication(open(p_pdf).read())
    # pdf.add_header('Content-Disposition', 'attachment', filename=name_pdf)
    xml = MIMEApplication(open(p_xml).read())
    xml.add_header('Content-Disposition', 'attachment', filename=name)
    msg.attach(MIMEText(html, 'html'))
    msg.attach(xml)
    #msg.attach(pdf)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login('etqm25@gmail.com', API_KEY)
    text = msg.as_string()
    server.sendmail('etqm25@gmail.com', 'etquizhpem@unl.edu.ec', text)
    server.quit()

    return True

@frappe.whitelist(allow_guest=True)
def save_file(cls,  empresa, name_pdf, name_xml, report, xml_element):
    ahora = datetime.datetime.now()
    year = str(ahora.year)
    if ahora.month < 10:
        month = '0'+ str(ahora.month)
    else:
        month = str(ahora.month)
    nuevaruta_c = NUEVA_RUTA + '/comprobantes/'+empresa +'/'+year+'/'+month
    if not os.path.exists(nuevaruta_c):
        os.makedirs(nuevaruta_c)
    file_ = 'true'
    f = open(nuevaruta_c + "/" + name_pdf, 'wb')
    f.write(report)
    f.close()
    f = open(nuevaruta_c + "/" + name_xml, 'wb')
    f.write(xml_element)
    f.close()

    commands.getoutput('rsync -az /home/noduxdev/.noduxenvs/nodux34auth/comprobantes/* /home/noduxdev/pruebas/static/comprobantes/')

    return file_
