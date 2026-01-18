from flask import Flask, request, jsonify
from flask_cors import CORS
from pos_backend import InventoryManager

app = Flask(__name__)
CORS(app)  # Permite requests desde tu frontend

inventory = InventoryManager('credentials.json', 'Inventario')

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
        result = inventory.process_sale(cart)
        return jsonify(result)
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)