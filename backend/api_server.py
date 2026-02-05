from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pos_backend import InventoryManager, ReceiptPrinter
import secrets
import os

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    app.config.update(
        SESSION_COOKIE_NAME='pos_session',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=False,   # change to True when HTTPS
        SESSION_COOKIE_PATH='/',      # 👈 THIS LINE
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 7,  # 7 days
        SESSION_REFRESH_EACH_REQUEST=True
    )

    CORS(app, supports_credentials=True)  # Importante: soportar credenciales

    CREDS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not CREDS_PATH:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set")

    if not os.path.isfile(CREDS_PATH):
        raise RuntimeError(f"Credentials file not found: {CREDS_PATH}")


    inventory = InventoryManager(CREDS_PATH, 'CentroComercialTB')

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({
                    'success': False,
                    'message': 'Usuario y contraseña son requeridos'
                }), 400
            
            result = inventory.authenticate_user(username, password)
            
            if result['success']:
                # Guardar usuario en sesión
                session['user'] = result['user']
                session.permanent = True
                
                return jsonify(result)
            else:
                return jsonify(result), 401
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        session.pop('user', None)
        return jsonify({'success': True, 'message': 'Sesión cerrada'})

    @app.route('/api/auth/check', methods=['GET'])
    def check_auth():
        """Verifica si hay sesión activa"""
        if 'user' in session:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': session['user']
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })

    @app.route('/api/users/create', methods=['POST'])
    def create_user():
        """Solo administradores pueden crear usuarios"""
        try:
            # Verificar que hay sesión activa y es admin
            if 'user' not in session or session['user']['role'] != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No autorizado'
                }), 403
            
            data = request.json
            result = inventory.create_user(
                username=data['username'],
                password=data['password'],
                role=data.get('role', 'vendedor'),
                nombre=data.get('nombre', '')
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/users', methods=['GET'])
    def get_users():
        """Solo administradores pueden ver usuarios"""
        try:
            if 'user' not in session or session['user']['role'] != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No autorizado'
                }), 403
            
            result = inventory.get_all_users()
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    # Middleware para proteger rutas
    def require_auth(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({
                    'success': False,
                    'message': 'No autorizado. Inicie sesión.'
                }), 401
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/api/inventory', methods=['GET'])
    def get_inventory():
        """Obtener todo el inventario"""
        try:
            data = inventory.get_inventory()
            print(data)
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/inventory/add', methods=['POST'])
    def add_product():
        try:
            data = request.json
            
            # Validar datos requeridos
            required_fields = ['codigo', 'nombre', 'costo', 'precio_1', 'unidad']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'Campo requerido faltante: {field}'
                    }), 400
            if data['precio_2'] == None:
                 data['precio_2'] = 0.0

            # Preparar datos del producto con valores por defecto
            product_data = {
                'codigo': data['codigo'],
                'nombre': data['nombre'],
                'cantidad': data.get('cantidad', 0),
                'costo': float(data['costo']),
                'precio_1': float(data['precio_1']),
                'minStock': data.get('minStock', 5),
                'unidad': data['unidad'],
                'precio_2': float(data['precio_2']),
            }
            
            # Guardar producto usando la clase de Google Sheets
            result = inventory.add_product(product_data)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

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
            print(cart)
            vendedor = request.json.get('vendedor', 'Sistema')

            result =  inventory.process_sale(cart, vendedor)

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

    @app.route('/api/sales/profit-analysis', methods=['GET'])
    def get_profit_analysis():
        try:
            period = request.args.get('period', 'today')  # today, week, month, custom
            custom_start = request.args.get('start_date')
            custom_end = request.args.get('end_date')
            
            result = inventory.get_profit_analysis(period, custom_start, custom_end)
            print(result)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    return app
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
app = create_app()
#if __name__ == '__main__':
#    app.run(host="0.0.0.0", debug=True, port=5000)