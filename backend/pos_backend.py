from concurrent.futures import ThreadPoolExecutor
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid

# Printer
from escpos.printer import Network
from decimal import Decimal, ROUND_HALF_UP

BUSINESS_TZ = ZoneInfo("America/Guayaquil")


class ReceiptPrinter: 
    def __init__(self):
        # Configure for RPT004 - adjust vendor/product ID for your printer
        # To find IDs: lsusb (Linux) or Device Manager (Windows)
        try:
            # USB Printer
            #self.printer = Usb(0x04b8, 0x0e14)  # Replace with your RPT004 IDs
            
            # OR Network Printer (if using WiFi/Ethernet)
            self.printer = Network("192.168.1.100")
            
            # OR File Printer (for testing - prints to file)
            # self.printer = File("/dev/usb/lp0")
            
        except Exception as e:
            print(f"Printer initialization error: {e}")
            self.printer = None
    
    def print_receipt(self, receipt_data):
        """Print receipt to thermal printer"""
        if not self.printer:
            return {'success': False, 'error': 'Printer not initialized'}
        
        try:
            business = receipt_data['business']
            sale = receipt_data['sale']
            items = receipt_data['items']
            totals = receipt_data['totals']
            
            # Set encoding
            self.printer.charcode('USA')
            
            # Header - Centered
            self.printer.set(align='center', text_type='B', width=2, height=2)
            self.printer.text(f"{business['name']}\n")
            
            self.printer.set(align='center', text_type='normal', width=1, height=1)
            self.printer.text(f"{business['address']}\n")
            self.printer.text(f"{business['RUC']}\n")

            # Separator
            self.printer.text("================================\n")
            
            # Sale Info - Left aligned
            self.printer.set(align='left')
            self.printer.text(f"Fecha: {sale['fecha']} {sale['hora']}\n")          
            self.printer.text("--------------------------------\n")
            
            # Items Header
            self.printer.set(text_type='B')
            self.printer.text(f"{'Producto':<20} {'Cant':>4} {'Total':>8}\n")
            self.printer.set(text_type='normal')
            self.printer.text("--------------------------------\n")
            
            # Items
            for item in items:
                # Product name (can wrap if long)
                name = item['product_name'][:20]
                self.printer.text(f"{name:<20}\n")
                
                # Quantity, price, total
                qty = item['quantity_sold']
                price = item['price']
                total = price * qty
                self.printer.text(f"  ${price:.2f} x {qty:>2}        ${total:>7.2f}\n")
            
            self.printer.text("================================\n")
            
            # Totals
            self.printer.set(text_type='B', width=2, height=2)
            self.printer.text(f"TOTAL:          ${totals['total']:>8.2f}\n")
            
            #self.printer.set(text_type='normal', width=1, height=1)
            #if totals['received'] > 0:
            #    self.printer.text(f"Recibido:       ${totals['received']:>8.2f}\n")
            #    self.printer.text(f"Cambio:         ${totals['change']:>8.2f}\n")
            
            self.printer.text("--------------------------------\n")
            
            # Footer - Centered
            self.printer.set(align='center')
            self.printer.text("\n")
            self.printer.set(text_type='B')
            self.printer.text("¡Gracias por su compra!\n")
            self.printer.text("\n")
            
            # Cut paper
            self.printer.cut()
            
            return {'success': True, 'message': 'Receipt printed successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

class InventoryManager:
    def __init__(self, credentials_file, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file, scope
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open(spreadsheet_name)
        self.sheet_inventory = self.spreadsheet.worksheet('Inventario')
        self.sheet_sales = self.spreadsheet.worksheet('Ventas')
        self.sheet_users = self.spreadsheet.worksheet('Usuarios')  # Nueva hoja
        self.printer = ReceiptPrinter()
    
    def hash_password(self, password):
        """Hash de contraseña con SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, role='vendedor', nombre=''):
        """Crea un nuevo usuario"""
        try:
            # Verificar si el usuario ya existe
            users = self.sheet_users.get_all_records()
            for user in users:
                if user['Usuario'].lower() == username.lower():
                    return {
                        'success': False,
                        'message': 'El usuario ya existe'
                    }
            
            # Hash de la contraseña
            hashed_password = self.hash_password(password)
            
            # Obtener siguiente ID
            next_id = len(users) + 1
            
            # Crear usuario
            row = [
                next_id,
                username,
                hashed_password,
                role,  # admin, vendedor, cajero
                nombre,
                'Si',  # Activo
                ''  # UltimoAcceso
            ]
            
            self.sheet_users.append_row(row)
            
            return {
                'success': True,
                'message': 'Usuario creado exitosamente',
                'user_id': next_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def authenticate_user(self, username, password):
        """Autentica un usuario"""
        try:
            users = self.sheet_users.get_all_records()
            hashed_password = self.hash_password(password)
            
            for user in users:
                if (user['Usuario'].lower() == username.lower() and 
                    user['Password'] == hashed_password and 
                    user['Activo'].lower() == 'si'):
                    
                    # Actualizar último acceso
                    user_row = users.index(user) + 2  # +2 porque fila 1 es header y index empieza en 0
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.sheet_users.update_cell(user_row, 7, now)  # Columna 7 es UltimoAcceso
                    
                    return {
                        'success': True,
                        'user': {
                            'id': user['ID'],
                            'username': user['Usuario'],
                            'role': user['Rol'],
                            'nombre': user['Nombre']
                        }
                    }
            
            return {
                'success': False,
                'message': 'Usuario o contraseña incorrectos'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_users(self):
        """Obtiene todos los usuarios (sin passwords)"""
        try:
            users = self.sheet_users.get_all_records()
            users_list = []
            
            for user in users:
                users_list.append({
                    'id': user['ID'],
                    'username': user['Usuario'],
                    'role': user['Rol'],
                    'nombre': user['Nombre'],
                    'activo': user['Activo'],
                    'ultimo_acceso': user.get('UltimoAcceso', '')
                })
            
            return {
                'success': True,
                'users': users_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_inventory(self):
        """Obtiene todo el inventario"""
        records = self.sheet_inventory.get_all_records()
        return records
    
    def add_product(self, product_data):
        """Agrega un nuevo producto a la hoja de Inventario"""
        try:
            now = datetime.now(BUSINESS_TZ)
            ultima_actualizacion = now.strftime('%Y-%m-%d %H:%M:%S')
            
            # Obtener el último ID para generar el siguiente
            all_records = self.sheet_inventory.get_all_records()
            next_id = len(all_records) + 1  # El siguiente ID es el total de registros + 1
            
            # Preparar fila para insertar
            # Estructura: ID, Codigo, Nombre, Cantidad, Costo, Precio, MinStock, UltimaActualizacion
            row = [
                next_id,
                product_data['codigo'],
                product_data['nombre'],
                product_data['cantidad'],
                product_data['unidad'],
                product_data['costo'],
                product_data['precio_1'],
                product_data['precio_2'],
                product_data['minStock'],
                ultima_actualizacion,

            ]
            
            print(f'Producto para insertar: {row}')
            
            # Insertar el producto
            self.sheet_inventory.append_row(row)
            
            return {
                'success': True,
                'message': 'Producto agregado exitosamente',
                'product_code': product_data['codigo'],
                'product_id': next_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Error al agregar producto: {str(e)}'
            }
    
    def get_product_by_code(self, code):
        """Busca un producto por código"""
        try:
            cell = self.sheet_inventory.find(code)
            row = self.sheet_inventory.row_values(cell.row)
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
    
    def update_stock(self, product_code, quantity_sold, price_type):
        """Actualiza el stock después de una venta"""
        try:
            print("Actualizando stock...")

            # Buscar el producto
            cell = self.sheet_inventory.find(product_code)
            row = cell.row
            
            print("No product")

            # Obtener datos del producto
            product_id = self.sheet_inventory.cell(row, 1).value
            product_name = self.sheet_inventory.cell(row, 3).value
            current_qty = float(self.sheet_inventory.cell(row, 4).value)
            unidad = self.sheet_inventory.cell(row, 5).value.lower()
            price_1 = float(self.sheet_inventory.cell(row, 7).value)
            price_2 = float(self.sheet_inventory.cell(row, 8).value)
            min_stock = float(self.sheet_inventory.cell(row, 9).value)
            quantity_sold = float(quantity_sold)

            print("Datos obtenidos")
            
            if unidad == "unidad" and not quantity_sold.is_integer():
                print("Unidad is not integer")
                return {
                    'success': False,
                    'error': 'Este producto solo se puede vender en unidades enteras'
                }

            # Verificar si hay suficiente stock
            if current_qty < quantity_sold:
                print("Datos obtenidos")
                return {
                    'success': False,
                    'error': 'Stock insuficiente'
                }
            
            # Calcular nueva cantidad
            new_qty = round(current_qty - quantity_sold, 3)
            
            # Actualizar en la hoja
            self.sheet_inventory.update_cell(row, 4, new_qty)
            
            # Actualizar timestamp
            timestamp = datetime.now(BUSINESS_TZ).strftime('%Y-%m-%d %H:%M:%S')
            self.sheet_inventory.update_cell(row, 10, timestamp)
            
            # Verificar si requiere alerta
            alert = new_qty <= min_stock

            # Verificar precio
            if price_type == "precio_2":
                selected_price = price_2
            else:
                selected_price = price_1
            
            print("Se ha actualizado el stock")

     
            return {
                    'success': True,
                    'product_id': product_id,
                    'product_code': product_code,
                    'product_name': product_name,
                    'price': selected_price,
                    'quantity_sold':quantity_sold,
                    'new_quantity': new_qty,
                    'alert': alert
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        
    def save_sale(self, sale_id, cart_items, total, vendedor='Sistema'):
        """Guarda el detalle de la venta en la hoja de Ventas"""
        try:
            now = datetime.now(BUSINESS_TZ)
            fecha = now.strftime('%Y-%m-%d')
            hora = now.strftime('%H:%M:%S')
            
            # Preparar filas para insertar
            rows = []
            for item in cart_items:
                row = [
                    sale_id,
                    fecha,
                    hora,
                    item['product_id'],
                    item['product_code'],
                    item['product_name'],
                    item['quantity_sold'],
                    item['price'],
                    item['price'] * item['quantity_sold'],  # Subtotal
                    total,
                    vendedor
                ]
                rows.append(row)
            print(f'Filas para insertar: {rows}')
            # Insertar todas las filas de la venta
            self.sheet_sales.append_rows(rows)
            
            return {
                'success': True,
                'sale_id': sale_id,
                'items_saved': len(rows)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        
    def process_sale(self, cart_items, vendedor='Sistema'):
        """Procesa una venta completa"""

        sale_id = f"VTA-{datetime.now(BUSINESS_TZ).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        results = []
        alerts = []
        total_sale = 0
        sale_details = []
        
        # Procesar cada producto        
        for item in cart_items:
            print(f"Processing {item['codigo']}")

            result = self.update_stock(
                item['codigo'],
                item['cantidad_vendida'],
                item['tipoPrecio']
            )
            
            if not result['success']:
                return{
                    'success': False,
                    'error': f"Error en {item['codigo']}: {result['error']}"
                }
            
            results.append(result)

            # Calcular total
            subtotal = result['price']*result['quantity_sold']

            total_sale += subtotal
            
            # Guardar detalles para el historial
            sale_details.append({
                'product_id': result['product_id'],
                'product_code': result['product_code'],
                'product_name': result['product_name'],
                'price': result['price'],
                'quantity_sold': result['quantity_sold']
            })
            
            # Verificar alertas
            if result.get('alert'):
                alerts.append({
                    'producto': result['product_name'],
                    'cantidad_restante': result['new_quantity']
                })

        print(f"Sales details: {sale_details}")
        
        # Prepare receipt data
        receipt_data = {
            'business': {
                'name': 'COMERCIAL TB',
                'address': 'Loja-San Lucas Av. Panamericana ',
                'RUC': 'RUC: 1102762885001'
            },
            'sale': {
                'id': sale_id,
                'fecha': datetime.now().strftime('%d/%m/%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
                'vendedor': vendedor
            },
            'items': cart_items,
            'totals': {
                'total': total_sale,
            }
        }

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks receipt
            #print_future = executor.submit(
            #    self.printer.print_receipt, 
            #    receipt_data
            #)
            save_future = executor.submit(
                self.save_sale, 
                sale_id, 
                sale_details, 
                total_sale, 
                vendedor
                )

            # Wait for BOTH to complete and get results
            #print_result = print_future.result()  # Blocks until print is done
            save_result = save_future.result()    # Blocks until save is done
        
        
        # Both tasks are now complete - check results
        #print("Both tasks have ended")
        #if not print_result['success']:
        #    return {
        #        'success': False,
        #        'message': f"Error imprimiendo recibo: {print_result.get('error')}"
        #    }

        if not save_result['success']:
            return {
                'success': False,
                'error': f"Venta procesada pero no se guardó en historial: {save_result['error']}"
            }
            
        return {
            'success': True,
            'sale_id': sale_id,
            'total': total_sale,
            'items': len(results),
            'results': results,
            'alerts': alerts
        }
    
    def get_sales_history(self, limit=None, date_from=None, date_to=None):
        """Obtiene el historial de ventas con filtros opcionales"""
        try:
            records = self.sheet_sales.get_all_records()
            
            # Filtrar por fecha si se especifica
            if date_from:
                records = [r for r in records if r['Fecha'] >= date_from]
            if date_to:
                records = [r for r in records if r['Fecha'] <= date_to]
            
            # Limitar cantidad de resultados
            if limit:
                records = records[-limit:]
            
            return records
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            return []
    
    def get_sales_summary(self, date=None):
        """Obtiene un resumen de ventas del día"""
        try:
            if date is None:
                date = datetime.now(BUSINESS_TZ).strftime('%Y-%m-%d')
            
            records = self.sheet_sales.get_all_records()
            daily_sales = [r for r in records if r['Fecha'] == date]
            
            if not daily_sales:
                return {
                    'date': date,
                    'total_sales': 0,
                    'total_amount': 0,
                    'items_sold': 0,
                    'unique_sales': 0
                }
            
            # Calcular estadísticas
            unique_sales = len(set(r['VentaID'] for r in daily_sales))
            total_items = sum(r['Cantidad'] for r in daily_sales)
            total_amount = sum(r['Subtotal'] for r in daily_sales)
            
            return {
                'date': date,
                'total_sales': unique_sales,
                'total_amount': total_amount,
                'items_sold': total_items,
                'sales': daily_sales
            }
            
        except Exception as e:
            return {
                'error': str(e)
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

    def get_profit_analysis(self, period='today', custom_start=None, custom_end=None):
        """Analiza las utilidades para cierre de caja por período"""
        try:
            from datetime import datetime, timedelta
            
            # Obtener ventas e inventario
            sales = self.sheet_sales.get_all_records()
            inventory = self.sheet_inventory.get_all_records()

            print(sales)
            print(inventory)
            
            # Diccionario de costos
            costs_dict = {item['Codigo']: float(item.get('Costo', 0)) for item in inventory}
            
            # Determinar rango de fechas según período
            now = datetime.now(BUSINESS_TZ)
            
            if period == 'today':
                start_date = now.replace(hour=0, minute=0, second=0)
                end_date = now.replace(hour=23, minute=59, second=59)
                period_label = f"Hoy - {now.strftime('%d/%m/%Y')}"
                
            elif period == 'week':
                # Inicio de semana (lunes)
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0)
                end_date = now.replace(hour=23, minute=59, second=59)
                period_label = f"Esta Semana ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')})"
                
            elif period == 'month':
                # Inicio de mes
                start_date = now.replace(day=1, hour=0, minute=0, second=0)
                end_date = now.replace(hour=23, minute=59, second=59)
                period_label = f"Este Mes - {now.strftime('%B %Y')}"
                
            elif period == 'custom' and custom_start and custom_end:
                start_date = datetime.strptime(custom_start, '%Y-%m-%d')
                end_date = datetime.strptime(custom_end, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                period_label = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            else:
                return {'success': False, 'error': 'Período no válido'}
            
            # Filtrar ventas por período
            filtered_sales = []
            for sale in sales:
                try:
                    sale_datetime = datetime.strptime(
                        f"{sale['Fecha']} {sale['Hora']}",
                        '%Y-%m-%d %H:%M:%S'
                    ).replace(tzinfo=BUSINESS_TZ)
                    
                    if start_date <= sale_datetime <= end_date:
                        filtered_sales.append(sale)
                except:
                    continue
            print("filtered sales")
            print(filtered_sales)

            # Calcular totales
            total_ingresos = Decimal("0.000")
            total_costos = Decimal("0.000")
            total_unidades = Decimal("0")
            ventas_detalle = []
            productos_vendidos = {}
            vendedores_stats = {}
            
            for sale in filtered_sales:
                codigo = sale['Codigo']
                cantidad = Decimal(str(sale['Cantidad']))
                precio_venta = Decimal(str(sale['PrecioUnitario']))
                costo_unitario = Decimal(str(costs_dict.get(codigo, 0)))
                vendedor = sale.get('Vendedor', 'Sistema')
                
                ingreso = (precio_venta * cantidad).quantize(Decimal("0.001"), ROUND_HALF_UP)
                costo = (costo_unitario * cantidad).quantize(Decimal("0.001"), ROUND_HALF_UP)
                utilidad = (ingreso - costo).quantize(Decimal("0.001"), ROUND_HALF_UP)
                
                utilidad = utilidad.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                
                total_ingresos += ingreso
                total_costos += costo
                total_unidades += cantidad
                
                # Detalle de venta
                ventas_detalle.append({
                    'fecha': sale['Fecha'],
                    'hora': sale['Hora'],
                    'producto': sale['Nombre'],
                    'cantidad': cantidad,
                    'precio_venta': precio_venta,
                    'costo_unitario': costo_unitario,
                    'ingreso': ingreso,
                    'costo': costo,
                    'utilidad': utilidad,
                    'vendedor': vendedor
                })
                
                # Agrupar por producto
                if codigo not in productos_vendidos:
                    productos_vendidos[codigo] = {
                        'producto': sale['Nombre'],
                        'codigo': codigo,
                        'cantidad': 0,
                        'ingresos': 0,
                        'costos': 0,
                        'utilidad': 0
                    }
                productos_vendidos[codigo]['cantidad'] += cantidad
                productos_vendidos[codigo]['ingresos'] += ingreso
                productos_vendidos[codigo]['costos'] += costo
                productos_vendidos[codigo]['utilidad'] += utilidad
                
                # Estadísticas por vendedor
                if vendedor not in vendedores_stats:
                    vendedores_stats[vendedor] = {
                        'vendedor': vendedor,
                        'ventas': 0,
                        'ingresos': 0,
                        'utilidad': 0
                    }
                vendedores_stats[vendedor]['ventas'] += 1
                vendedores_stats[vendedor]['ingresos'] += ingreso
                vendedores_stats[vendedor]['utilidad'] += utilidad
            
            utilidad_neta = (total_ingresos - total_costos).quantize(Decimal("0.001"), ROUND_HALF_UP)
            margen_total = ((utilidad_neta / total_ingresos * 100)).quantize(Decimal("0.001"), ROUND_HALF_UP)if total_ingresos > 0 else Decimal("0.000")
            
            # Convertir diccionarios a listas y ordenar
            productos_list = sorted(productos_vendidos.values(), key=lambda x: x['utilidad'], reverse=True)
            vendedores_list = sorted(vendedores_stats.values(), key=lambda x: x['ingresos'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'periodo': period_label,
                    'total_ingresos': round(total_ingresos, 2),
                    'total_costos': round(total_costos, 2),
                    'utilidad_neta': round(utilidad_neta, 2),
                    'margen_total': round(margen_total, 2),
                    'total_ventas': len(filtered_sales),
                    'total_unidades': total_unidades,
                    'ticket_promedio': round(total_ingresos / len(filtered_sales), 2) if filtered_sales else 0,
                    'productos_vendidos': productos_list[:10],  # Top 10
                    'vendedores': vendedores_list,
                    'ventas_detalle': ventas_detalle
                }
            }
            
        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

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