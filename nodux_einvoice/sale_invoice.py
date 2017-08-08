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
import requests
#validacion de email
#from validate_email import validate_email

tipoIdentificacion = {
    'RUC' : '04',
    'Cedula' : '05',
    'Pasaporte' : '06',
    'Consumidor Final' : '07',
}

ambiente = {
    'Pruebas' : '1',
    'Produccion' : '2'
}

emision = {
    'Normal' : '1'
}

def validate(doc, event):
    # if doc.fisic_invoice == True:
    #     pass
    # elif doc.lote == False:
    action_generate_invoice(doc)
    #establecer conexion con base de datos
    connect_db(doc)
    doc.docstatus = 1
    return

def get_invoice_element(doc):
        company = frappe.db.get_value("Company", {'company_name':doc.company}, ["street", "no_resolucion", "mandatory_accounting", "vat_number"], as_dict=1)
        party = frappe.db.get_value("Customer", {'customer_name':doc.customer_name}, ["type_document", "customer_name", "tax_id", "street"], as_dict=1)

        infoFactura = etree.Element('infoFactura')
        date = datetime.strptime(doc.posting_date, '%Y-%m-%d')
        etree.SubElement(infoFactura, 'fechaEmision').text = date.strftime('%d/%m/%Y')
        if company.street:
            etree.SubElement(infoFactura, 'dirEstablecimiento').text = company.street
        if company.contribuyente_especial_nro:
            etree.SubElement(infoFactura, 'contribuyenteEspecial').text = company.no_resolucion
        if company.mandatory_accounting:
            etree.SubElement(infoFactura, 'obligadoContabilidad').text = company.mandatory_accounting
        else:
            etree.SubElement(infoFactura, 'obligadoContabilidad').text = 'NO'
        if party.type_document:
            etree.SubElement(infoFactura, 'tipoIdentificacionComprador').text = tipoIdentificacion[party.type_document]
        else:
            frappe.throw("No ha configurado el tipo de identificacion del cliente")
        etree.SubElement(infoFactura, 'razonSocialComprador').text = party.customer_name
        etree.SubElement(infoFactura, 'identificacionComprador').text = party.tax_id
        if party.street:
            etree.SubElement(infoFactura, 'direccionComprador').text = party.street
        etree.SubElement(infoFactura, 'totalSinImpuestos').text = '%.2f' % (doc.base_total)
        etree.SubElement(infoFactura, 'totalDescuento').text = '0.00' #descuento esta incluido en el precio poner 0.0 por defecto

        #totalConImpuestos
        totalConImpuestos = etree.Element('totalConImpuestos')

        for tax in doc.taxes:
            #if tax.tax_group in ['vat', 'vat0', 'ice', 'other']:
            totalImpuesto = etree.Element('totalImpuesto')
            #de acuerdo a niif
            if str('{:.0f}'.format(tax.rate)) == '12':
                codigoPorcentaje = '2'
                codigo = '2'
            if str('{:.0f}'.format(tax.rate)) == '0':
                codigoPorcentaje = '0'
                codigo = '2'
            if str('{:.0f}'.format(tax.rate)) == '14':
                codigoPorcentaje = '3'
                codigo = '2'
            if tax.rate == None:
                codigoPorcentaje = '6'
            etree.SubElement(totalImpuesto, 'codigo').text = codigo
            etree.SubElement(totalImpuesto, 'codigoPorcentaje').text = codigoPorcentaje
            etree.SubElement(totalImpuesto, 'baseImponible').text = '{:.2f}'.format(tax.total - tax.tax_amount)
            etree.SubElement(totalImpuesto, 'valor').text = '{:.2f}'.format(tax.tax_amount)
            totalConImpuestos.append(totalImpuesto)

        infoFactura.append(totalConImpuestos)
        etree.SubElement(infoFactura, 'propina').text = '0.00'
        etree.SubElement(infoFactura, 'importeTotal').text = '{:.2f}'.format(doc.base_grand_total)
        etree.SubElement(infoFactura, 'moneda').text = 'DOLAR'

        # if doc.formas_pago_sri:
        #     if doc.formas_pago_sri.name == 'NINGUNA':
        #         pass
        #     else:
        #         pagos = etree.Element('pagos')
        #         pago = etree.Element('pago')
        #         etree.SubElement(pago, 'formaPago').text = doc.formas_pago_sri.code
        #         etree.SubElement(pago, 'total').text = '{:.2f}'.format(doc.total_amount)
        #         if doc.payment_term:
        #             day = 0
        #             month = 0
        #             week = 0
        #             for l in doc.payment_term.lines:
        #                 if l.days:
        #                     day += l.days
        #                 if l.months:
        #                     month += l.months
        #                 if l.weeks:
        #                     week += l.weeks
        #                 if day >= 0 :
        #                     etree.SubElement(pago, 'plazo').text = str(day)
        #                     etree.SubElement(pago, 'unidadTiempo').text = 'dias'
        #                 if month > 0:
        #                     etree.SubElement(pago, 'plazo').text = str(month)
        #                     etree.SubElement(pago, 'unidadTiempo').text = 'meses'
        #                 if week > 0:
        #                     etree.SubElement(pago, 'plazo').text = str(month)
        #                     etree.SubElement(pago, 'unidadTiempo').text = 'semanas'
        #
        #         pagos.append(pago)
        #         infoFactura.append(pagos)
        return infoFactura

def get_tax_element(doc):
    company = frappe.db.get_value("Company", {'company_name':doc.company}, ["ambiente", "emision", "vat_number", "company_name", "commercial_name", 'street'], as_dict=1)
    party = frappe.db.get_value("Customer", {'customer_name':doc.customer_name}, ["type_document", "customer_name", "tax_id", "street"], as_dict=1)
    infoTributaria = etree.Element('infoTributaria')
    etree.SubElement(infoTributaria, 'ambiente').text = ambiente[company.ambiente]
    etree.SubElement(infoTributaria, 'tipoEmision').text = emision[company.emision]
    etree.SubElement(infoTributaria, 'razonSocial').text = company.company_name
    if company.commercial_name:
        etree.SubElement(infoTributaria, 'nombreComercial').text = company.commercial_name
    etree.SubElement(infoTributaria, 'ruc').text = company.vat_number
    etree.SubElement(infoTributaria, 'claveAcceso').text = generate_access_key(doc, company.vat_number, company.ambiente, doc.naming_series, company.emision )
    etree.SubElement(infoTributaria, 'codDoc').text = "01"
    etree.SubElement(infoTributaria, 'estab').text = "001"#doc.naming_series[0:3]
    etree.SubElement(infoTributaria, 'ptoEmi').text ="001" #doc.naming_series[4:7]
    etree.SubElement(infoTributaria, 'secuencial').text = "0000"+doc.name[5:10]#doc.naming_series[8:17]
    if company.street:
        etree.SubElement(infoTributaria, 'dirMatriz').text = company.street

    return infoTributaria

def generate_access_key(doc, vat_number, t_ambiente, number, t_emision):
    date = datetime.strptime(doc.posting_date, '%Y-%m-%d')
    f = date.strftime('%d%m%Y')
    t_cbte = "01"
    ruc = vat_number
    t_amb = ambiente[t_ambiente]
    n_cbte= number
    cod= "73625814"
    t_ems= emision[t_emision]
    #quitar cuando se tenga la secuencia
    #numero_cbte= "001001000001115"+(n_cbte.replace('-','').replace("S","").replace("I","").replace("N", "").replace("V",""))
    numero_cbte = "0010010000"+doc.name[5:10]
    #unimos todos los datos en una sola cadena
    key_temp = f+t_cbte+ruc+t_amb+numero_cbte+cod+t_ems
    #recorremos la cadena para ir guardando en una lista de enteros
    key = []
    for c in key_temp:
        key.append(int(c))

    key.reverse()
    factor = [2,3,4,5,6,7]
    stage1 = sum([n*factor[i%6] for i,n in enumerate(key)])
    stage2 = stage1 % 11
    digit = 11 - (stage2)
    if digit == 11:
        digit =0
    if digit == 10:
        digit = 1
    digit=str(digit)
    access_key= key_temp + digit
    return access_key

def get_detail_element(doc):
    detalles = etree.Element('detalles')

    for item in doc.items:
        detalle = etree.Element('detalle')
        data_item = frappe.db.get_value("Item", {'item_name':item.item_name}, ["item_code"], as_dict=1)
        etree.SubElement(detalle, 'codigoPrincipal').text = data_item.item_code
        etree.SubElement(detalle, 'descripcion').text = item.description
        etree.SubElement(detalle, 'cantidad').text = '%.2f' % (item.qty)
        etree.SubElement(detalle, 'precioUnitario').text = '%.2f' % (item.rate)
        etree.SubElement(detalle, 'descuento').text = '0.00'
        etree.SubElement(detalle, 'precioTotalSinImpuesto').text = '%.2f' % (item.amount)
        impuestos = etree.Element('impuestos')
        impuesto = etree.Element('impuesto')
        etree.SubElement(impuesto, 'codigo').text = "2"

        for tax in doc.taxes:
            if str('{:.0f}'.format(tax.rate)) == '12':
                codigoPorcentaje = '2'
            if str('{:.0f}'.format(tax.rate*100)) == '0':
                codigoPorcentaje = '0'
            if str('{:.0f}'.format(tax.rate*100)) == '14':
                codigoPorcentaje = '3'
            if tax.rate == None:
                codigoPorcentaje = '6'

            etree.SubElement(impuesto, 'codigoPorcentaje').text = codigoPorcentaje
            etree.SubElement(impuesto, 'tarifa').text = str('{:.0f}'.format(tax.rate))
            etree.SubElement(impuesto, 'baseImponible').text = '{:.2f}'.format(item.amount)
            etree.SubElement(impuesto, 'valor').text = '{:.2f}'.format(item.amount*(tax.rate/100))
        impuestos.append(impuesto)

        detalle.append(impuestos)
        detalles.append(detalle)
        return detalles

def generate_xml_invoice(doc):
    factura = etree.Element('factura')
    factura.set("id", "comprobante")
    factura.set("version", "1.1.0")

    # generar infoTributaria
    infoTributaria = get_tax_element(doc)
    factura.append(infoTributaria)

    # generar infoFactura
    infoFactura = get_invoice_element(doc)
    factura.append(infoFactura)

    #generar detalles
    detalles = get_detail_element(doc)
    factura.append(detalles)
    print etree.tostring(factura, pretty_print = True)
    return factura

def action_generate_invoice(doc):

    PK12 = u'No ha configurado los datos de la empresa. Dirijase a: \n Empresa -> NODUX WS'
    AUTHENTICATE_ERROR = u'Error de datos de conexión al autorizador de \nfacturacion electrónica.\nVerifique: USUARIO Y CONTRASEÑA .'
    ACTIVE_ERROR = u"Ud. no se encuentra activo, verifique su pago. \nComuníquese con NODUX"
    WAIT_FOR_RECEIPT = 3
    TITLE_NOT_SENT = u'No se puede enviar el comprobante electronico al SRI'
    MESSAGE_SEQUENCIAL = u'Los comprobantes electrónicos deben ser enviados al SRI en orden secuencial'
    MESSAGE_TIME_LIMIT = u'Se ha excedido el límite de tiempo. Los comprobantes electrónicos deben ser enviados al SRI para su autorización, en un plazo máximo de 24 horas'

    company = frappe.db.get_value("Company", {'company_name':doc.company}, ['company_name', 'vat_number', 'ambiente','emision'], as_dict=1)
    usuario = base64.encodestring(frappe.client.get_password("Company", doc.company, 'user_ws'))
    password_u= base64.encodestring(frappe.client.get_password("Company", doc.company, 'password_w_s'))
    # usuario = frappe.client.get_password("Company", doc.company, 'user_ws')
    # password_u= frappe.client.get_password("Company", doc.company, 'password_w_s')
    access_key = generate_access_key(doc, company.vat_number, company.ambiente, doc.naming_series, company.emision)
    # address_xml = web_service(doc)
    # s= xmlrpclib.ServerProxy(address_xml)

    #response = requests.get('http://192.168.1.43:8000/api/method/nodux_auth.prueba')


    name = company.company_name
    name_l = name.lower()
    name_l = name_l.replace(' ','_')
    name_r = replace_character(doc, name_l)
    name_c = name_r+'.p12'

    #authenticate, send_m, active = s.model.nodux_electronic_invoice_auth.conexiones.authenticate(usuario, password_u, {})
    response = requests.get("http://192.168.1.43:8000/api/method/nodux_auth.authenticate", params={
    "user":usuario,
    "password":password_u
    })
    authenticate = response.json().get("message")[0]
    send_m = response.json().get("message")[1]
    active = response.json().get("message")[2]

    if authenticate == '1':
        pass
    else:
        frappe.throw(AUTHENTICATE_ERROR)

    if active == '1':
        frappe.throw(ACTIVE_ERROR)
    else:
        pass

    nuevaruta = s.model.nodux_electronic_invoice_auth.conexiones.save_pk12(name_l, {})

    factura1 = generate_xml_invoice(doc)
    factura = etree.tostring(factura1, encoding = 'utf8', method = 'xml')
    a = s.model.nodux_electronic_invoice_auth.conexiones.validate_xml(factura, 'out_invoice', {})

    if a:
        frappe.throw(a)

    file_pk12 = base64.encodestring(nuevaruta+'/'+name_c)
    file_check = (nuevaruta+'/'+name_c)
    password = base64.encodestring(frappe.client.get_password("Company", doc.company, "password_pk12"))
    error = s.model.nodux_electronic_invoice_auth.conexiones.check_digital_signature(file_check,{})
    if error == '1':
        frappe.throw('No se ha encontrado el archivo de firma digital (.p12)')

    signed_document= s.model.nodux_electronic_invoice_auth.conexiones.apply_digital_signature(factura, file_pk12, password,{})
    #envio al sri para recepcion del comprobante electronico
    result = s.model.nodux_electronic_invoice_auth.conexiones.send_receipt(signed_document, {})
    if result != True:
        frappe.throw(result)
    time.sleep(WAIT_FOR_RECEIPT)
    # solicitud al SRI para autorizacion del comprobante electronico
    doc_xml, m, auth, path, numero, num = s.model.nodux_electronic_invoice_auth.conexiones.request_authorization(access_key, name_r, 'out_invoice', signed_document,{})
    if doc_xml is None:
        msg = ' '.join(m)
        raise m

    if auth == 'NO AUTORIZADO':
        doc.estado_sri = "NO AUTORIZADO"
        doc.mensaje = doc_xml
    else:
        doc.estado_sri = "AUTORIZADO"
        send_mail_invoice(doc, doc_xml, access_key, send_m, s)

    return

def web_service(doc):
    CONEXION = 'UD NO HA CONFIGURADO LOS DATOS DE CONEXION CON EL WS, \nCOMUNIQUESE CON EL ADMINISTRADOR DEL SISTEMA'
    company = frappe.db.get_value("Company", {'company_name':doc.company}, ['cabecera', 'direccion', 'puerto'], as_dict=1)

    usuario = frappe.client.get_password("Company", doc.company, "usuario")
    pass_db = frappe.client.get_password("Company", doc.company, "pass_db")
    name_db = frappe.client.get_password("Company", doc.company, "name_db")

    if company:
        address = company.cabecera+usuario+":"+pass_db+"@"+company.direccion+":"+company.puerto+"/"+name_db
        return address
    else:
        frappe.throw(CONEXION)

def replace_character(doc, cadena):
        reemplazo = {u"Â":"A", u"Á":"A", u"À":"A", u"Ä":"A", u"É":"E", u"È":"E", u"Ê":"E",u"Ë":"E",
            u"Í":"I",u"Ì":"I",u"Î":"I",u"Ï":"I",u"Ó":"O",u"Ò":"O",u"Ö":"O",u"Ô":"O",u"Ú":"U",u"Ù":"U",u"Ü":"U",
            u"Û":"U",u"á":"a",u"à":"a",u"â":"a",u"ä":"a",u"é":"e",u"è":"e",u"ê":"e",u"ë":"e",u"í":"i",u"ì":"i",
            u"ï":"i",u"î":"i",u"ó":"o",u"ò":"o",u"ô":"o",u"ö":"o",u"ú":"u",u"ù":"u",u"ü":"u",u"û":"u",u"ñ":"n",
            u"Ñ":"N", u"Nº":"No", u"nº":"No"}
        regex = re.compile("(%s)" % "|".join(map(re.escape, reemplazo.keys())))
        nueva_cadena = regex.sub(lambda x: str(reemplazo[x.string[x.start():x.end()]]), cadena)
        return nueva_cadena

def send_mail_invoice(doc, xml_element, access_key, send_m, s, server="localhost"):
    MAIL= u"Ud no ha configurado el correo del cliente. Diríjase a: \nTerceros->General->Medios de Contacto"
    company = frappe.db.get_value("Company", {'company_name':doc.company}, ['company_name', 'vat_number', 'email'], as_dict=1)
    customer = frappe.db.get_value("Customer", {'customer_name':doc.customer}, ['customer_name', 'email'], as_dict=1)
    empresa = replace_character(doc, company.company_name)
    empresa = empresa.replace(' ','_')
    empresa = empresa.lower()

    ahora = datetime.now()
    year = str(ahora.year)
    client = replace_character(doc, customer.customer_name) #reemplazo self.party.name
    client = client.upper()
    empresa_ = replace_character(doc, company.company_name) #reemplazo self.company.party.name
    ruc = company.vat_number

    if ahora.month < 10:
        month = '0'+ str(ahora.month)
    else:
        month = str(ahora.month)

    tipo_comprobante = "out_invoice"
    if tipo_comprobante == 'out_invoice':
        tipo = 'fact_'
        n_tipo = "FACTURA"
    if tipo_comprobante == 'in_withholding':
        tipo = 'c_r_'
        n_tipo = "COMPROBANTE DE RETENCION"
    if tipo_comprobante == 'out_credit_note':
        tipo = 'n_c_'
        n_tipo = "NOTA DE CREDITO"
    if tipo_comprobante == 'out_debit_note':
        tipo = 'n_d_'
        n_tipo = "NOTA DE DEBITO"

    ruc = access_key[10:23]
    est = access_key[24:27]
    emi= access_key[27:30]
    sec = access_key[30:39]
    num_fac = est+'-'+emi+'-'+sec
    numero = ruc+'_'+num_fac
    name_pdf = tipo+numero+ '.pdf'
    name_xml = tipo+numero + '.xml'
    #nuevaruta =os.getcwd() +'/comprobantes/'+empresa+'/'+year+'/'+month +'/'
    nr = s.model.nodux_electronic_invoice_auth.conexiones.path_files(ruc, {})
    nuevaruta = nr +empresa+'/'+year+'/'+month +'/'

    new_save = 'comprobantes/'+empresa+'/'+year+'/'+month +'/'
    doc.path_xml = new_save+name_xml
    doc.numero_autorizacion = access_key
    doc.path_pdf = new_save+name_pdf
    #doc.save()

    if customer.email != '':
        to_email= customer.email
    else :
        frappe.throw(MAIL)

    if company.email != "":
        from_email = company.email
    else:
        frappe.throw(MAIL)
    # if send_m == '1':
    #     from_email = f_e
    # else :
    #     from_email = "nodux.ec@gmail.com"
    name = access_key + ".xml"
    #reporte = xmlrpclib.Binary(report[1])
    xml_element = replace_character(doc, xml_element)
    xml = xmlrpclib.Binary(xml_element.replace('><', '>\n<'))

    save_files = s.model.nodux_electronic_invoice_auth.conexiones.save_file(empresa, name_pdf, name_xml, xml, xml,{})
    p_xml = nuevaruta + name_xml
    p_pdf = nuevaruta + name_pdf
    # es_valido = validate_email(to_email, verify=True)
    # if es_valido == True:
    #     s.model.nodux_electronic_invoice_auth.conexiones.send_mail(name_pdf, name, p_xml, p_pdf, from_email, to_email, n_tipo, num_fac, client, empresa_, ruc, {})
    s.model.nodux_electronic_invoice_auth.conexiones.send_mail(name_pdf, name, p_xml, p_pdf, from_email, to_email, n_tipo, num_fac, client, empresa_, ruc, {})

    return True

def connect_db(doc):

    address_xml = web_service(doc)
    s= xmlrpclib.ServerProxy(address_xml)

    customer = frappe.db.get_value("Customer", {'customer_name':doc.customer_name}, ['customer_name', 'tax_id', 'email'], as_dict=1)
    company = frappe.db.get_value("Company", {'company_name':doc.company}, ['company_name', 'vat_number', 'email'],as_dict=1)
    nombre = customer.customer_name
    cedula = customer.tax_id
    ruc = company.vat_number
    nombre_e = company.company_name
    tipo = "out_invoice"
    fecha = str(doc.posting_date)
    empresa = company.company_name
    est = doc.numero_autorizacion[24:27]
    emi= doc.numero_autorizacion[27:30]
    sec = doc.numero_autorizacion[30:39]
    numero = str(est)+"-"+str(emi)+"-"+str(sec)
    path_xml = doc.path_xml
    path_pdf = doc.path_pdf
    estado = doc.estado_sri
    auth = doc.numero_autorizacion
    email_e= company.email
    email = customer.email
    total = str(doc.base_grand_total)

    if doc.estado_sri == 'AUTORIZADO':
        s.model.nodux_electronic_invoice_auth.conexiones.connect_db(nombre, cedula, ruc, nombre_e, tipo, fecha, empresa, numero, path_xml, path_pdf,estado, auth, email, email_e, total, {})
