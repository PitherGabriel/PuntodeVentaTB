"""
Generador de XML para Facturas Electrónicas según esquema SRI
"""
from lxml import etree
from datetime import datetime
import random
from config import SRIConfig

class XMLGenerator:
    
    @staticmethod
    def calcular_digito_verificador(clave_sin_dv):
        """
        Calcula el dígito verificador módulo 11
        Según especificación del SRI
        """
        multiplicador = 7
        suma = 0
        
        for digito in clave_sin_dv:
            suma += int(digito) * multiplicador
            multiplicador -= 1
            if multiplicador < 2:
                multiplicador = 7
        
        residuo = suma % 11
        resultado = 11 - residuo
        
        if resultado == 11:
            return 0
        elif resultado == 10:
            return 1
        else:
            return resultado
    
    @staticmethod
    def generar_clave_acceso(fecha_emision, secuencial):
        """
        Genera clave de acceso de 49 dígitos según especificación SRI
        
        Estructura:
        [Fecha][TipoDoc][RUC][Ambiente][Serie][Secuencial][CodNum][TipoEmision][DV]
        """
        # Formatear fecha DDMMAAAA
        fecha_str = fecha_emision.strftime('%d%m%Y')
        
        # Tipo de documento (01 = Factura)
        tipo_doc = '01'
        
        # RUC del emisor
        ruc = SRIConfig.RUC_EMISOR
        
        # Ambiente (1 = Pruebas, 2 = Producción)
        ambiente = str(SRIConfig.AMBIENTE_ACTUAL)
        
        # Serie (establecimiento + punto emisión)
        serie = SRIConfig.CODIGO_ESTABLECIMIENTO + SRIConfig.CODIGO_PUNTO_EMISION
        
        # Secuencial (9 dígitos)
        secuencial_str = str(secuencial).zfill(9)
        
        # Código numérico aleatorio (8 dígitos)
        codigo_numerico = str(random.randint(10000000, 99999999))
        
        # Tipo de emisión (1 = Normal)
        tipo_emision = str(SRIConfig.TIPO_EMISION_NORMAL)
        
        # Construir clave sin dígito verificador (48 dígitos)
        clave_sin_dv = (
            fecha_str +
            tipo_doc +
            ruc +
            ambiente +
            serie +
            secuencial_str +
            codigo_numerico +
            tipo_emision
        )
        
        # Calcular dígito verificador
        dv = XMLGenerator.calcular_digito_verificador(clave_sin_dv)
        
        # Clave completa de 49 dígitos
        clave_acceso = clave_sin_dv + str(dv)
        
        return clave_acceso
    
    @staticmethod
    def generar_factura_xml(datos_venta, datos_cliente, secuencial):
        """
        Genera el XML de la factura según esquema XSD del SRI
        Versión 1.1.0
        
        Args:
            datos_venta: dict con información de la venta
            datos_cliente: dict con información del cliente
            secuencial: int número secuencial de la factura
        
        Returns:
            str: XML generado como string
        """
        
        fecha_emision = datetime.now()
        clave_acceso = XMLGenerator.generar_clave_acceso(fecha_emision, secuencial)
        
        # Crear elemento raíz
        factura = etree.Element(
            "factura",
            id="comprobante",
            version="1.1.0"
        )
        
        # === INFORMACIÓN TRIBUTARIA ===
        info_tributaria = etree.SubElement(factura, "infoTributaria")
        
        etree.SubElement(info_tributaria, "ambiente").text = str(SRIConfig.AMBIENTE_ACTUAL)
        etree.SubElement(info_tributaria, "tipoEmision").text = str(SRIConfig.TIPO_EMISION_NORMAL)
        etree.SubElement(info_tributaria, "razonSocial").text = SRIConfig.RAZON_SOCIAL
        etree.SubElement(info_tributaria, "nombreComercial").text = SRIConfig.NOMBRE_COMERCIAL
        etree.SubElement(info_tributaria, "ruc").text = SRIConfig.RUC_EMISOR
        etree.SubElement(info_tributaria, "claveAcceso").text = clave_acceso
        etree.SubElement(info_tributaria, "codDoc").text = "01"  # 01 = Factura
        etree.SubElement(info_tributaria, "estab").text = SRIConfig.CODIGO_ESTABLECIMIENTO
        etree.SubElement(info_tributaria, "ptoEmi").text = SRIConfig.CODIGO_PUNTO_EMISION
        etree.SubElement(info_tributaria, "secuencial").text = str(secuencial).zfill(9)
        etree.SubElement(info_tributaria, "dirMatriz").text = SRIConfig.DIR_MATRIZ
        
        # === INFORMACIÓN FACTURA ===
        info_factura = etree.SubElement(factura, "infoFactura")
        
        etree.SubElement(info_factura, "fechaEmision").text = fecha_emision.strftime('%d/%m/%Y')
        etree.SubElement(info_factura, "dirEstablecimiento").text = SRIConfig.DIR_ESTABLECIMIENTO
        
        if SRIConfig.CONTRIBUYENTE_ESPECIAL:
            etree.SubElement(info_factura, "contribuyenteEspecial").text = SRIConfig.CONTRIBUYENTE_ESPECIAL
        
        etree.SubElement(info_factura, "obligadoContabilidad").text = SRIConfig.OBLIGADO_CONTABILIDAD
        
        # Información del cliente
        etree.SubElement(info_factura, "tipoIdentificacionComprador").text = datos_cliente['tipo_identificacion']
        etree.SubElement(info_factura, "razonSocialComprador").text = datos_cliente['razon_social']
        etree.SubElement(info_factura, "identificacionComprador").text = datos_cliente['identificacion']
        
        if datos_cliente.get('direccion'):
            etree.SubElement(info_factura, "direccionComprador").text = datos_cliente['direccion']
        
        # Totales
        subtotal = datos_venta['subtotal_sin_impuestos']
        descuento = datos_venta.get('descuento_total', 0.00)
        iva_total = datos_venta['iva_total']
        total = datos_venta['total']
        
        etree.SubElement(info_factura, "totalSinImpuestos").text = f"{subtotal:.2f}"
        etree.SubElement(info_factura, "totalDescuento").text = f"{descuento:.2f}"
        
        # Total con impuestos
        total_con_impuestos = etree.SubElement(info_factura, "totalConImpuestos")
        
        # IVA
        total_impuesto = etree.SubElement(total_con_impuestos, "totalImpuesto")
        etree.SubElement(total_impuesto, "codigo").text = "2"  # 2 = IVA
        etree.SubElement(total_impuesto, "codigoPorcentaje").text = datos_venta['codigo_porcentaje_iva']
        etree.SubElement(total_impuesto, "baseImponible").text = f"{subtotal:.2f}"
        etree.SubElement(total_impuesto, "valor").text = f"{iva_total:.2f}"
        
        etree.SubElement(info_factura, "propina").text = "0.00"
        etree.SubElement(info_factura, "importeTotal").text = f"{total:.2f}"
        etree.SubElement(info_factura, "moneda").text = "DOLAR"
        
        # Formas de pago
        pagos = etree.SubElement(info_factura, "pagos")
        pago = etree.SubElement(pagos, "pago")
        etree.SubElement(pago, "formaPago").text = datos_venta.get('forma_pago', '01')  # 01 = Sin sistema financiero
        etree.SubElement(pago, "total").text = f"{total:.2f}"
        
        # === DETALLES ===
        detalles = etree.SubElement(factura, "detalles")
        
        for item in datos_venta['items']:
            detalle = etree.SubElement(detalles, "detalle")
            
            etree.SubElement(detalle, "codigoPrincipal").text = item['codigo']
            etree.SubElement(detalle, "descripcion").text = item['descripcion']
            etree.SubElement(detalle, "cantidad").text = f"{item['cantidad']:.6f}"
            etree.SubElement(detalle, "precioUnitario").text = f"{item['precio_unitario']:.6f}"
            etree.SubElement(detalle, "descuento").text = f"{item.get('descuento', 0.00):.2f}"
            etree.SubElement(detalle, "precioTotalSinImpuesto").text = f"{item['precio_total_sin_impuesto']:.2f}"
            
            # Impuestos del detalle
            impuestos = etree.SubElement(detalle, "impuestos")
            impuesto = etree.SubElement(impuestos, "impuesto")
            
            etree.SubElement(impuesto, "codigo").text = "2"  # IVA
            etree.SubElement(impuesto, "codigoPorcentaje").text = item['codigo_porcentaje_iva']
            etree.SubElement(impuesto, "tarifa").text = item['tarifa_iva']
            etree.SubElement(impuesto, "baseImponible").text = f"{item['precio_total_sin_impuesto']:.2f}"
            etree.SubElement(impuesto, "valor").text = f"{item['valor_iva']:.2f}"
        
        # === INFORMACIÓN ADICIONAL ===
        if datos_venta.get('info_adicional'):
            info_adicional = etree.SubElement(factura, "infoAdicional")
            for campo in datos_venta['info_adicional']:
                campo_adicional = etree.SubElement(info_adicional, "campoAdicional", nombre=campo['nombre'])
                campo_adicional.text = campo['valor']
        
        # Convertir a string con declaración XML
        xml_string = etree.tostring(
            factura,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
        
        return xml_string, clave_acceso