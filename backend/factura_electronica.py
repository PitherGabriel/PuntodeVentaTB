# Código para enviar al SRI
from zeep import Client
from zeep.transports import Transport
from requests import Session
import base64

class SRIClient:
    def __init__(self, ambiente='pruebas'):
        """
        ambiente: 'pruebas' o 'produccion'
        """
        if ambiente == 'pruebas':
            self.url_recepcion = 'https://celcert.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
            self.url_autorizacion = 'https://celcert.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
        else:
            self.url_recepcion = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
            self.url_autorizacion = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
        
        # Configurar cliente SOAP
        session = Session()
        session.verify = True  # Verificar certificados SSL
        transport = Transport(session=session)
        
        self.client_recepcion = Client(self.url_recepcion, transport=transport)
        self.client_autorizacion = Client(self.url_autorizacion, transport=transport)
    
    def enviar_comprobante(self, xml_firmado):
        """
        Envía el XML firmado al SRI para recepción
        """
        try:
            # Convertir XML a bytes y luego a base64
            xml_bytes = xml_firmado.encode('utf-8')
            
            # Llamar al servicio
            response = self.client_recepcion.service.validarComprobante(xml_bytes)
            
            return {
                'success': response.estado == 'RECIBIDA',
                'estado': response.estado,
                'comprobantes': response.comprobantes,
                'mensaje': response.mensaje if hasattr(response, 'mensaje') else ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def consultar_autorizacion(self, clave_acceso):
        """
        Consulta el estado de autorización de un comprobante
        """
        try:
            response = self.client_autorizacion.service.autorizacionComprobante(clave_acceso)
            
            if hasattr(response, 'autorizaciones') and response.autorizaciones:
                autorizacion = response.autorizaciones.autorizacion[0]
                
                return {
                    'success': True,
                    'estado': autorizacion.estado,
                    'numeroAutorizacion': autorizacion.numeroAutorizacion,
                    'fechaAutorizacion': autorizacion.fechaAutorizacion,
                    'ambiente': autorizacion.ambiente,
                    'comprobante': autorizacion.comprobante,
                    'mensajes': autorizacion.mensajes if hasattr(autorizacion, 'mensajes') else []
                }
            else:
                return {
                    'success': False,
                    'error': 'No se encontró la autorización'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Ejemplo de uso
sri = SRIClient(ambiente='pruebas')

# 1. Enviar comprobante
resultado_envio = sri.enviar_comprobante(xml_firmado)

if resultado_envio['success']:
    print("✅ Comprobante recibido por el SRI")
    
    # 2. Esperar un momento (el SRI procesa)
    import time
    time.sleep(3)
    
    # 3. Consultar autorización
    resultado_auth = sri.consultar_autorizacion(clave_acceso)
    
    if resultado_auth['success'] and resultado_auth['estado'] == 'AUTORIZADO':
        print(f"✅ Factura AUTORIZADA")
        print(f"Número de autorización: {resultado_auth['numeroAutorizacion']}")
    else:
        print(f"❌ Factura NO autorizada: {resultado_auth.get('error', 'Error desconocido')}")
else:
    print(f"❌ Error enviando: {resultado_envio['error']}")