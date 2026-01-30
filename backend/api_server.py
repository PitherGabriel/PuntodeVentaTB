from flask import Flask, request, jsonify
from flask_cors import CORS
from pos_backend import InventoryManager
#from sri_manager import SRIManager  # NUEVO
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permite requests desde tu frontend

inventory = InventoryManager('credentials.json', 'CentroComercialTB')
# NUEVO - Gestor de facturación SRI
#sri_manager = SRIManager()

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Obtener todo el inventario"""
    try:
        data = inventory.get_inventory()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/product/<code>', methods=['GET'])
def get_product(code):
    """Obtener un producto específico"""
    product = inventory.get_product_by_code(code)
    if product:
        return jsonify({'success': True, 'data': product})
    return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404

@app.route('/api/sale', methods=['POST'])
def process_sale():
    """Procesar una venta"""
    try:
        cart = request.json.get('cart', [])
        vendedor = request.json.get('vendedor', 'Sistema')

        result = inventory.process_sale(cart, vendedor)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/history', methods=['GET'])
def get_sales_history():
    """Obtener historial de ventas"""
    try:
        limit = request.args.get('limit', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        history = inventory.get_sales_history(limit, date_from, date_to)
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Obtener resumen de ventas del día"""
    try:
        date = request.args.get('date')  # Formato: YYYY-MM-DD
        summary = inventory.get_sales_summary(date)
        return jsonify({'success': True, 'data': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Obtener alertas de stock bajo"""
    try:
        alerts = inventory.get_low_stock_alerts()
        return jsonify({'success': True, 'alerts': alerts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

"""
@app.route('/api/sale-with-invoice-sri', methods=['POST'])
def process_sale_with_invoice_sri():
    # Procesar venta con factura electrónica SRI
    try:
        cart = request.json.get('cart', [])
        vendedor = request.json.get('vendedor', 'Sistema')
        cliente = request.json.get('cliente', None)
        
        # Validar datos del cliente
        if not cliente:
            return jsonify({
                'success': False,
                'error': 'Datos del cliente requeridos para facturar'
            }), 400
        
        # Validar campos obligatorios del cliente
        campos_requeridos = ['identificacion', 'razon_social', 'email']
        for campo in campos_requeridos:
            if not cliente.get(campo):
                return jsonify({
                    'success': False,
                    'error': f'Campo {campo} del cliente es obligatorio'
                }), 400
        
        # 1. Procesar venta normal (inventario + historial)
        sale_result = inventory.process_sale(cart, vendedor)
        
        if not sale_result['success']:
            return jsonify(sale_result), 400
        
        # 2. Emitir factura electrónica SRI
        venta_pos = {
            'cart': cart,
            'vendedor': vendedor,
            'sale_id': sale_result['sale_id'],
            'cliente': cliente
        }
        
        invoice_result = sri_manager.emitir_factura(venta_pos, cliente)
        
        if not invoice_result['success']:
            return jsonify({
                'success': False,
                'error': f"Venta procesada pero factura falló: {invoice_result.get('error', 'Error desconocido')}",
                'sale_id': sale_result['sale_id'],
                'detalles_error': invoice_result
            }), 500
        
        # 3. TODO: Guardar datos de factura en Google Sheets hoja "Facturas"
        
        # 4. TODO: Enviar email al cliente con XML y RIDE
        
        return jsonify({
            'success': True,
            'sale': sale_result,
            'invoice': invoice_result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
"""

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)