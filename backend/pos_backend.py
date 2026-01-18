import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

class InventoryManager:
    def __init__(self, credentials_file, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file, scope
        )
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open(spreadsheet_name).sheet1
        
    def get_inventory(self):
        """Obtiene todo el inventario"""
        records = self.sheet.get_all_records()
        return records
    
    def get_product_by_code(self, code):
        """Busca un producto por código"""
        try:
            cell = self.sheet.find(code)
            row = self.sheet.row_values(cell.row)
            return {
                'id': row[0],
                'codigo': row[1],
                'nombre': row[2],
                'cantidad': int(row[3]),
                'precio': float(row[4]),
                'minStock': int(row[5])
            }
        except:
            return None
    
    def update_stock(self, product_code, quantity_sold):
        """Actualiza el stock después de una venta"""
        try:
            # Buscar el producto
            cell = self.sheet.find(product_code)
            row = cell.row
            
            # Obtener cantidad actual
            current_qty = int(self.sheet.cell(row, 4).value)
            min_stock = int(self.sheet.cell(row, 6).value)
            
            # Verificar si hay suficiente stock
            if current_qty < quantity_sold:
                return {
                    'success': False,
                    'error': 'Stock insuficiente'
                }
            
            # Calcular nueva cantidad
            new_qty = current_qty - quantity_sold
            
            # Actualizar en la hoja
            self.sheet.update_cell(row, 4, new_qty)
            
            # Actualizar timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.sheet.update_cell(row, 7, timestamp)
            
            # Verificar si requiere alerta
            alert = new_qty <= min_stock
            
            return {
                'success': True,
                'new_quantity': new_qty,
                'alert': alert,
                'product_name': self.sheet.cell(row, 3).value
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_sale(self, cart_items):
        """Procesa una venta completa"""
        results = []
        alerts = []
        
        for item in cart_items:
            result = self.update_stock(
                item['codigo'],
                item['cantidad_vendida']
            )
            
            results.append(result)
            
            if result.get('alert'):
                alerts.append({
                    'producto': result['product_name'],
                    'cantidad_restante': result['new_quantity']
                })
        
        return {
            'success': all(r['success'] for r in results),
            'results': results,
            'alerts': alerts
        }
    
    def get_low_stock_alerts(self):
        """Obtiene todos los productos con stock bajo"""
        records = self.get_inventory()
        alerts = []
        
        for record in records:
            if record['Cantidad'] <= record['MinStock']:
                alerts.append({
                    'codigo': record['Codigo'],
                    'nombre': record['Nombre'],
                    'cantidad': record['Cantidad'],
                    'minimo': record['MinStock']
                })
        
        return alerts


# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar
    inventory = InventoryManager(
        'credenciales.json',
        'Inventario_MiTienda'
    )
    
    # Ejemplo de venta
    venta = [
        {'codigo': 'CAM001', 'cantidad_vendida': 2},
        {'codigo': 'PAN001', 'cantidad_vendida': 1}
    ]
    
    resultado = inventory.process_sale(venta)
    
    if resultado['success']:
        print("✅ Venta procesada exitosamente")
        
        if resultado['alerts']:
            print("\n⚠️ ALERTAS DE STOCK BAJO:")
            for alert in resultado['alerts']:
                print(f"  - {alert['producto']}: {alert['cantidad_restante']} unidades")
    else:
        print("❌ Error procesando la venta")