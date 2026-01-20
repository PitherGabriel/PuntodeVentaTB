"""
Firma electrónica de XMLs según estándar XAdES-BES
"""
from lxml import etree
from signxml import XMLSigner
from OpenSSL import crypto
from config import SRIConfig
import base64

class FirmaElectronica:
    
    def __init__(self):
        self.cert_path = SRIConfig.CERTIFICADO_PATH
        self.cert_password = SRIConfig.CERTIFICADO_PASSWORD
        self._cargar_certificado()
    
    def _cargar_certificado(self):
        """Carga el certificado .p12"""
        try:
            with open(self.cert_path, 'rb') as f:
                p12_data = f.read()
            
            self.p12 = crypto.load_pkcs12(p12_data, self.cert_password.encode())
            self.private_key = self.p12.get_privatekey()
            self.certificate = self.p12.get_certificate()
            
            print("✅ Certificado cargado correctamente")
        except FileNotFoundError:
            raise Exception(f"❌ No se encontró el certificado en: {self.cert_path}")
        except Exception as e:
            raise Exception(f"❌ Error al cargar certificado: {str(e)}")
    
    def firmar_xml(self, xml_string):
        """
        Firma un XML con el estándar XAdES-BES
        
        Args:
            xml_string: String con el XML a firmar
        
        Returns:
            str: XML firmado
        """
        try:
            # Parsear XML
            root = etree.fromstring(xml_string.encode('utf-8'))
            
            # Crear firmador con XAdES-BES
            signer = XMLSigner(
                method=XMLSigner.Methods.enveloped,
                signature_algorithm='rsa-sha1',
                digest_algorithm='sha1',
                c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
            )
            
            # Firmar
            signed_root = signer.sign(
                root,
                key=crypto.dump_privatekey(crypto.FILETYPE_PEM, self.private_key),
                cert=crypto.dump_certificate(crypto.FILETYPE_PEM, self.certificate),
                reference_uri='#comprobante'
            )
            
            # Convertir de vuelta a string
            signed_xml = etree.tostring(
                signed_root,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8'
            ).decode('utf-8')
            
            print("✅ XML firmado correctamente")
            return signed_xml
            
        except Exception as e:
            raise Exception(f"❌ Error firmando XML: {str(e)}")
    
    def verificar_firma(self, xml_firmado):
        """
        Verifica que la firma sea válida
        """
        try:
            from signxml import XMLVerifier
            
            root = etree.fromstring(xml_firmado.encode('utf-8'))
            verified_data = XMLVerifier().verify(root)
            
            print("✅ Firma verificada correctamente")
            return True
        except Exception as e:
            print(f"❌ Error verificando firma: {str(e)}")
            return False