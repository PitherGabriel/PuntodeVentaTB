"""
Configuración para Facturación Electrónica SRI
"""
import os
from datetime import datetime

class SRIConfig:
    # Datos del emisor (TU EMPRESA)
    RUC_EMISOR = "1102762885001"  # CAMBIAR por tu RUC
    RAZON_SOCIAL = "CENTRO COMERCIAL TB"  # CAMBIAR
    NOMBRE_COMERCIAL = "Mi Tienda"  # CAMBIAR
    DIR_MATRIZ = "LOJA/LOJA/SAN LUCAS/AKAKANA JUNTO AL CENTRO DE SALUD PICHIG"  # CAMBIAR
    DIR_ESTABLECIMIENTO = "LOJA / LOJA / SAN LUCAS / AKAKANA- JUNTO AL CENTRO DE SALUD PICHIG"  # CAMBIAR
    
    # Establecimiento y punto de emisión
    CODIGO_ESTABLECIMIENTO = "001"
    CODIGO_PUNTO_EMISION = "001"
    
    # Contribuyente especial (si aplica)
    CONTRIBUYENTE_ESPECIAL = None  # O número de resolución
    OBLIGADO_CONTABILIDAD = "NO"  # SI o NO
    
    # Ambiente
    AMBIENTE_PRUEBAS = 1
    AMBIENTE_PRODUCCION = 2
    AMBIENTE_ACTUAL = AMBIENTE_PRUEBAS  # Cambiar a producción cuando esté listo
    
    # Tipo de emisión
    TIPO_EMISION_NORMAL = 1
    
    # URLs del SRI
    if AMBIENTE_ACTUAL == AMBIENTE_PRUEBAS:
        URL_RECEPCION = "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"
        URL_AUTORIZACION = "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl"
    else:
        URL_RECEPCION = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"
        URL_AUTORIZACION = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl"
    
    # Certificado digital
    CERTIFICADO_PATH = "certificado.p12"
    CERTIFICADO_PASSWORD = "tu_password_aqui"  # CAMBIAR
    
    # Directorio para almacenar XMLs
    DIR_XML_GENERADOS = "xml_generados"
    DIR_XML_FIRMADOS = "xml_firmados"
    DIR_XML_AUTORIZADOS = "xml_autorizados"
    DIR_XML_RECHAZADOS = "xml_rechazados"
    
    @classmethod
    def crear_directorios(cls):
        """Crea los directorios necesarios si no existen"""
        for directorio in [cls.DIR_XML_GENERADOS, cls.DIR_XML_FIRMADOS, 
                          cls.DIR_XML_AUTORIZADOS, cls.DIR_XML_RECHAZADOS]:
            os.makedirs(directorio, exist_ok=True)