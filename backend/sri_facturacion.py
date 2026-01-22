"""
Cliente SOAP para comunicación con Web Services del SRI
"""
from zeep import Client
from zeep.transports import Transport
from requests import Session
import time
from lxml import etree
from config import SRIConfig
import os

class SRIClient:
    
    def __init__(self):
        """Inicializa el cliente SOAP del SRI"""
        # Configurar sesión HTTP
        session = Session()
        session.verify = True
        transport = Transport(session=session)
        
        # Crear clientes SOAP
        try:
            self.client_recepcion = Client(
                SRIConfig.URL_RECEPCION,
                transport=transport
            )
            self.client_autorizacion = Client(
                SRIConfig.URL_AUTORIZACION,
                transport=transport
            )
            
            ambiente = "PRUEBAS" if SRIConfig.AMBIENTE_ACTUAL == 1 else "PRODUCCIÓN"
            print(f"✅ Cliente SRI iniciado - Ambiente: {ambiente}")
            
        except Exception as e:
            raise Exception(f"❌ Error al conectar con el SRI: {str(e)}")
    
    def enviar_comprobante(self, xml_firmado):
        """
        Envía el comprobante firmado al SRI para recepción
        
        Args:
            xml_firmado: String con el XML firmado
        
        Returns:
            dict con resultado de la recepción
        """
        try:
            # Convertir XML a bytes
            xml_bytes = xml_firmado.encode('utf-8')
            
            # Llamar al servicio
            print("📤 Enviando comprobante al SRI...")
            response = self.client_recepcion.service.validarComprobante(xml_bytes)
            
            # Procesar respuesta
            estado = response.estado if hasattr(response, 'estado') else 'ERROR'
            
            resultado = {
                'success': estado == 'RECIBIDA',
                'estado': estado,
                'mensaje': ''
            }
            
            # Si fue rechazado, obtener errores
            if estado == 'DEVUELTA' and hasattr(response, 'comprobantes'):
                if response.comprobantes and hasattr(response.comprobantes, 'comprobante'):
                    comprobante = response.comprobantes.comprobante[0]
                    if hasattr(comprobante, 'mensajes'):
                        errores = []
                        for mensaje in comprobante.mensajes.mensaje:
                            error_info = {
                                'identificador': mensaje.identificador if hasattr(mensaje, 'identificador') else '',
                                'mensaje': mensaje.mensaje if hasattr(mensaje, 'mensaje') else '',
                                'tipo': mensaje.tipo if hasattr(mensaje, 'tipo') else '',
                                'informacion_adicional': mensaje.informacionAdicional if hasattr(mensaje, 'informacionAdicional') else ''
                            }
                            errores.append(error_info)
                        resultado['errores'] = errores
                        resultado['mensaje'] = errores[0]['mensaje'] if errores else 'Error desconocido'
            
            if resultado['success']:
                print(f"✅ Comprobante RECIBIDO por el SRI")
            else:
                print(f"❌ Comprobante RECHAZADO: {resultado['mensaje']}")
            
            return resultado
            
        except Exception as e:
            return {
                'success': False,
                'estado': 'ERROR',
                'mensaje': f'Error al enviar comprobante: {str(e)}'
            }
    
    def consultar_autorizacion(self, clave_acceso, intentos_maximos=10, tiempo_espera=3):
        """
        Consulta el estado de autorización de un comprobante
        
        Args:
            clave_acceso: Clave de acceso del comprobante (49 dígitos)
            intentos_maximos: Número máximo de intentos
            tiempo_espera: Segundos entre intentos
        
        Returns:
            dict con resultado de la autorización
        """
        print(f"🔍 Consultando autorización...")
        
        for intento in range(intentos_maximos):
            try:
                # Esperar antes de consultar (excepto en el primer intento)
                if intento > 0:
                    print(f"⏳ Esperando {tiempo_espera} segundos... (Intento {intento + 1}/{intentos_maximos})")
                    time.sleep(tiempo_espera)
                
                # Consultar autorización
                response = self.client_autorizacion.service.autorizacionComprobante(clave_acceso)
                
                # Verificar si hay autorizaciones
                if not hasattr(response, 'autorizaciones') or not response.autorizaciones:
                    continue
                
                # Obtener primera autorización
                autorizacion = response.autorizaciones.autorizacion[0]
                estado = autorizacion.estado if hasattr(autorizacion, 'estado') else 'ERROR'
                
                resultado = {
                    'success': estado == 'AUTORIZADO',
                    'estado': estado,
                    'clave_acceso': clave_acceso
                }
                
                # Si está autorizado
                if estado == 'AUTORIZADO':
                    resultado['numero_autorizacion'] = autorizacion.numeroAutorizacion
                    resultado['fecha_autorizacion'] = str(autorizacion.fechaAutorizacion)
                    resultado['ambiente'] = autorizacion.ambiente
                    resultado['comprobante_xml'] = autorizacion.comprobante
                    
                    # Extraer mensajes/advertencias
                    if hasattr(autorizacion, 'mensajes'):
                        advertencias = []
                        for mensaje in autorizacion.mensajes.mensaje:
                            advertencias.append({
                                'identificador': mensaje.identificador if hasattr(mensaje, 'identificador') else '',
                                'mensaje': mensaje.mensaje if hasattr(mensaje, 'mensaje') else '',
                                'tipo': mensaje.tipo if hasattr(mensaje, 'tipo') else ''
                            })
                        resultado['advertencias'] = advertencias
                    
                    print(f"✅ Comprobante AUTORIZADO")
                    print(f"   Número autorización: {resultado['numero_autorizacion']}")
                    print(f"   Fecha: {resultado['fecha_autorizacion']}")
                    return resultado
                
                # Si fue rechazado
                elif estado in ['NO AUTORIZADO', 'RECHAZADO']:
                    errores = []
                    if hasattr(autorizacion, 'mensajes'):
                        for mensaje in autorizacion.mensajes.mensaje:
                            errores.append({
                                'identificador': mensaje.identificador if hasattr(mensaje, 'identificador') else '',
                                'mensaje': mensaje.mensaje if hasattr(mensaje, 'mensaje') else '',
                                'tipo': mensaje.tipo if hasattr(mensaje, 'tipo') else ''
                            })
                    resultado['errores'] = errores
                    resultado['mensaje'] = errores[0]['mensaje'] if errores else 'Comprobante no autorizado'
                    
                    print(f"❌ Comprobante NO AUTORIZADO: {resultado['mensaje']}")
                    return resultado
                
            except Exception as e:
                if intento == intentos_maximos - 1:
                    return {
                        'success': False,
                        'estado': 'ERROR',
                        'mensaje': f'Error consultando autorización: {str(e)}'
                    }
        
        # Si llegamos aquí, se agotaron los intentos
        return {
            'success': False,
            'estado': 'TIMEOUT',
            'mensaje': 'Se agotó el tiempo de espera para la autorización'
        }
    
    def guardar_xml(self, xml_contenido, clave_acceso, directorio):
        """
        Guarda un XML en el directorio especificado
        """
        try:
            filepath = os.path.join(directorio, f"{clave_acceso}.xml")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_contenido)
            print(f"💾 XML guardado: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Error guardando XML: {str(e)}")
            return None