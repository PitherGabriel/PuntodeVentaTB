import React, { useState, useEffect } from 'react';
import {
  ShoppingCart,
  Package,
  AlertTriangle,
  Plus, Minus,
  Trash2,
  Search, History,
  TrendingUp,
  Check,
  X, Loader,
  PackagePlus,
  CircleDollarSign
} from 'lucide-react';


// Pantalla de Login
const LoginScreen = ({
  handleLogin,
  loginForm,
  setLoginForm,
  loginError,
  isLoggingIn
}) => (
  <div className="min-h-screen bg-linear-to-br from-white-600 to-white-800 flex items-center justify-center p-4">
    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
      <div className="text-center mb-8">
        <div className="inline-block p-4 rounded-full mb-5">
          <img src='logo.png' className='h-35 mx-auto'></img>
        </div>
        <h1 className="text-3xl font-bold text-gray-800">Comercial TB</h1>
        <p className="text-gray-600 mt-2">Inicia sesión para continuar</p>
      </div>

      {loginError && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-4">
          {loginError}
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Usuario
          </label>
          <input
            type="text"
            required
            value={loginForm.username}
            onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ingrese su usuario"
            disabled={isLoggingIn}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Contraseña
          </label>
          <input
            type="password"
            required
            value={loginForm.password}
            onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ingrese su contraseña"
            disabled={isLoggingIn}
          />
        </div>

        <button
          type="submit"
          disabled={isLoggingIn}
          className={`w-full py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${isLoggingIn
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-[#008cc8] text-white hover:bg-[#016996]'
            }`}
        >
          {isLoggingIn ? (
            <>
              <Loader className="animate-spin" size={20} />
              Iniciando sesión...
            </>
          ) : (
            'Iniciar Sesión'
          )}
        </button>
      </form>
    </div>
  </div>
);

const POSSystem = () => {

  // Al inicio del componente POSSystem, agregar estados
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const [inventory, setInventory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [activeTab, setActiveTab] = useState('pos'); // pos, inventario, inventory-add, history, summary
  const [salesHistory, setSalesHistory] = useState([]);
  //const [salesSummary, setSalesSummary] = useState(null);
  const [vendedor, setVendedor] = useState('Sistema');
  const [receivedMoney, setReceivedMoney] = useState('');
  const [processingSale, setProcessingSale] = useState(false);
  const [notification, setNotification] = useState(null);

  // Estados para nuevo producto
  const [newProduct, setNewProduct] = useState({
    nombre: '',
    costo: '',
    porcentajeGanancia: '',
    cantidad: '',
    minStock: ''
  });

  // Estados para filtros de historial
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');

  // Estados para facturación
  //const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  //const [processingInvoice, setProcessingInvoice] = useState(false);
  //const [invoiceResult, setInvoiceResult] = useState(null);
  const [clienteData, setClienteData] = useState({
    identificacion: '',
    razon_social: '',
    direccion: '',
    email: '',
    telefono: ''
  });

  // Estados para calculo de utilidades
  const [profitAnalysis, setProfitAnalysis] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('today');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

  const API_URL = '/api';

  // Verificar autenticación al cargar
  useEffect(() => {
    checkAuth();
  }, []);

  // Cargar inventario
  useEffect(() => {
    loadInventory();
  }, []);

  // Acitivar alerta de inventario 
  useEffect(() => {
    const lowStock = inventory.filter(item => item.cantidad <= item.minStock);
    setAlerts(lowStock);
  }, [inventory]);

  // Notificaciones
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000); // Auto-hide after 3 seconds
  };

  const loadProfitAnalysis = async (period = selectedPeriod) => {
    try {
      let url = `${API_URL}/sales/profit-analysis?period=${period}`;

      if (period === 'custom' && customStartDate && customEndDate) {
        url += `&start_date=${customStartDate}&end_date=${customEndDate}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        setProfitAnalysis(data.data);
      }
    } catch (error) {
      console.error('Error cargando análisis de utilidades:', error);
    }
  };

  const loadInventory = async () => {
    try {
      const response = await fetch(`${API_URL}/inventory`);
      const data = await response.json();
      if (data.success) {
        const formattedInventory = data.data.map(item => ({
          id: item.ID,
          nombre: item.Nombre,
          cantidad: item.Cantidad,
          precio: parseFloat(item.Precio),
          costo: parseFloat(item.Costo || 0),
          minStock: item.MinStock,
          codigo: item.Codigo
        }));
        setInventory(formattedInventory);
      }
      setIsLoading(false);
    } catch (error) {
      console.error('Error cargando inventario:', error);
      setIsLoading(false);
    }
  };

  const loadSalesHistory = async (limit = 50) => {
    try {
      console.log("History requested")
      const response = await fetch(`${API_URL}/sales/history?limit=${limit}`);
      const data = await response.json();
      console.log(data)
      if (data.success) {
        setSalesHistory(data.data);
      }
    } catch (error) {
      console.error('Error cargando historial:', error);
    }
  };

  /*
  const loadSalesSummary = async (date = null) => {
    try {
      const url = date ? `${API_URL}/sales/summary?date=${date}` : `${API_URL}/sales/summary`;
      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        setSalesSummary(data.data);
      }
    } catch (error) {
      console.error('Error cargando resumen:', error);
    }
  };
  */

  // Generar código único basado en el nombre
  const generateProductCode = (nombre) => {
    if (!nombre) return '';

    // Tomar las primeras 3 letras del nombre (sin espacios)
    const cleanName = nombre.replace(/\s+/g, '').toUpperCase();
    const prefix = cleanName.substring(0, 3);

    // Generar 5 dígitos aleatorios
    const randomNum = Math.floor(10000 + Math.random() * 90000);

    return `${prefix}${randomNum}`;
  };

  // Calcular precio de venta
  const calculateSalePrice = (costo, porcentaje) => {
    if (!costo || !porcentaje) return 0;
    const costoNum = parseFloat(costo);
    const porcentajeNum = parseFloat(porcentaje);
    return (costoNum * (1 + porcentajeNum / 100)).toFixed(2);
  };

  // Agregar nuevo producto
  const addNewProduct = async () => {
    if (!newProduct.nombre || !newProduct.costo || !newProduct.porcentajeGanancia) {
      showNotification('Por favor complete los campos obligatorios: Nombre, Costo y Porcentaje de Ganancia', 'error');
      return;
    }

    try {
      const codigo = generateProductCode(newProduct.nombre);
      const precioVenta = calculateSalePrice(newProduct.costo, newProduct.porcentajeGanancia);

      const productData = {
        codigo: codigo,
        nombre: newProduct.nombre,
        cantidad: parseInt(newProduct.cantidad) || 0,
        costo: parseFloat(newProduct.costo),
        precio: parseFloat(precioVenta),
        minStock: parseInt(newProduct.minStock) || 5
      };

      const response = await fetch(`${API_URL}/inventory/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData)
      });

      const result = await response.json();

      if (result.success) {
        showNotification(`Producto agregado exitosamente!\nCódigo: ${codigo}`, 'success');
        setNewProduct({
          nombre: '',
          costo: '',
          porcentajeGanancia: '',
          cantidad: '',
          minStock: ''
        });
        loadInventory();
      } else {
        alert('Error al agregar producto: ' + result.message);
      }
    } catch (error) {
      console.error('Error agregando producto:', error);
      alert('Error al agregar producto');
    }
  };

  // Agregar producto al carrito
  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);

    if (product.cantidad === 0) {
      alert('¡Producto sin stock!');
      return;
    }

    if (existingItem) {
      if (existingItem.cantidadVendida >= product.cantidad) {
        alert('¡No hay suficiente stock!');
        return;
      }
      setCart(cart.map(item =>
        item.id === product.id
          ? { ...item, cantidadVendida: item.cantidadVendida + 1 }
          : item
      ));
    } else {
      setCart([...cart, { ...product, cantidadVendida: 1 }]);
    }
  };

  // Actualizar cantidad de productos en carrito
  const updateCartQuantity = (productId, delta) => {
    const product = inventory.find(p => p.id === productId);
    const cartItem = cart.find(item => item.id === productId);

    const newQuantity = cartItem.cantidadVendida + delta;

    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }

    if (newQuantity > product.cantidad) {
      alert('¡No hay suficiente stock!');
      return;
    }

    setCart(cart.map(item =>
      item.id === productId
        ? { ...item, cantidadVendida: newQuantity }
        : item
    ));
  };

  // Eliminar producto de carrito
  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.id !== productId));
  };

  const processSaleWithInvoice = async () => {
    if (cart.length === 0) {
      alert('El carrito está vacío');
      return;
    }

    if (!clienteData.identificacion || !clienteData.razon_social || !clienteData.email) {
      alert('Por favor complete todos los campos obligatorios del cliente:\n- Identificación\n- Razón Social\n- Email');
      return;
    }

    setProcessingInvoice(true);
    setInvoiceResult(null);

    try {
      const cartData = cart.map(item => ({
        codigo: item.codigo,
        cantidad_vendida: item.cantidadVendida,
        nombre: item.nombre,
        precio: item.precio
      }));

      const response = await fetch(`${API_URL}/sale-with-invoice-sri`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cart: cartData,
          vendedor: vendedor,
          cliente: clienteData
        })
      });

      const result = await response.json();

      if (result.success) {
        const updatedInventory = inventory.map(item => {
          const cartItem = cart.find(c => c.id === item.id);
          if (cartItem) {
            return {
              ...item,
              cantidad: item.cantidad - cartItem.cantidadVendida
            };
          }
          return item;
        });

        setInventory(updatedInventory);
        setInvoiceResult(result.invoice);

        let message = `✅ FACTURA ELECTRÓNICA AUTORIZADA\n\n`;
        message += `📄 Número: ${result.invoice.numero_factura}\n`;
        message += `🔑 Autorización: ${result.invoice.numero_autorizacion}\n`;
        message += `💰 Total: $${result.invoice.total.toFixed(2)}\n`;
        message += `📅 Fecha: ${result.invoice.fecha_autorizacion}\n`;
        message += `🌐 Ambiente: ${result.invoice.ambiente === 'PRODUCCION' ? 'Producción' : 'Pruebas'}\n`;

        if (result.invoice.advertencias && result.invoice.advertencias.length > 0) {
          message += '\n⚠️ Advertencias:\n';
          result.invoice.advertencias.forEach(adv => {
            message += `• ${adv}\n`;
          });
        }

        alert(message);
        setCart([]);
        setReceivedMoney('');
        setShowInvoiceModal(false);
        resetClienteData();
      } else {
        let errorMessage = '❌ Error al procesar la factura\n\n';
        errorMessage += result.message || 'Error desconocido';

        if (result.details) {
          errorMessage += '\n\nDetalles:\n';
          if (Array.isArray(result.details)) {
            result.details.forEach(detail => {
              errorMessage += `• ${detail}\n`;
            });
          } else {
            errorMessage += result.details;
          }
        }

        alert(errorMessage);
      }
    } catch (error) {
      console.error('Error en facturación:', error);
      alert('❌ Error al procesar la factura electrónica:\n\n' + error.message);
    } finally {
      setProcessingInvoice(false);
    }
  };

  const resetClienteData = () => {
    setClienteData({
      identificacion: '',
      razon_social: '',
      direccion: '',
      email: '',
      telefono: ''
    });
    setInvoiceResult(null);
  };

  // Procesar venta simple
  const processSale = async () => {
    if (cart.length === 0) {
      showNotification('El carrito está vacío', 'error');
      return;
    }

    setProcessingSale(true);

    try {
      const cartData = cart.map(item => ({
        codigo: item.codigo,
        cantidad_vendida: item.cantidadVendida,
        nombre: item.nombre,
        precio: item.precio
      }));

      const response = await fetch(`${API_URL}/sale`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cart: cartData,
          vendedor: currentUser?.nombre
        })
      });

      const result = await response.json();

      if (result.success) {
        const updatedInventory = inventory.map(item => {
          const cartItem = cart.find(c => c.id === item.id);
          if (cartItem) {
            return {
              ...item,
              cantidad: item.cantidad - cartItem.cantidadVendida
            };
          }
          return item;
        });

        setInventory(updatedInventory);
        showNotification('¡Venta procesada exitosamente!', 'success');
        setCart([]);
        setReceivedMoney('');

      }
    } catch (error) {
      console.error('Error procesando venta:', error);
      showNotification('Error al procesar la venta', 'error');
    } finally {
      setProcessingSale(false);
    }
  };

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + (item.precio * item.cantidadVendida), 0);
  };

  const calculateChange = () => {
    const total = calculateTotal();
    const received = parseFloat(receivedMoney) || 0;
    return received - total;
  };

  // Filtrar productos por búsqueda
  const filteredInventory = searchTerm.trim() === ''
    ? []
    : inventory.filter(item =>
      item.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.codigo.toLowerCase().includes(searchTerm.toLowerCase())
    );

  // Filtrar ventas por fecha
  const filteredSalesHistory = salesHistory.filter(sale => {
    if (!filterStartDate && !filterEndDate) return true;

    const saleDate = new Date(sale.Fecha);
    const startDate = filterStartDate ? new Date(filterStartDate) : null;
    const endDate = filterEndDate ? new Date(filterEndDate) : null;

    if (startDate && endDate) {
      return saleDate >= startDate && saleDate <= endDate;
    } else if (startDate) {
      return saleDate >= startDate;
    } else if (endDate) {
      return saleDate <= endDate;
    }
    return true;
  });

  // Comprobar si existe una autentificación de usuario 
  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_URL}/auth/check`, {
        credentials: 'include'
      });
      const data = await response.json();

      if (data.authenticated) {
        setIsAuthenticated(true);
        setCurrentUser(data.user);
        setVendedor(data.user.nombre || data.user.username);
        loadInventory();
      }
    } catch (error) {
      console.error('Error verificando autenticación:', error);
    }
  };

  // Inicio de sesión del usuario
  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError('');

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(loginForm)
      });

      const data = await response.json();

      if (data.success) {
        setIsAuthenticated(true);
        setCurrentUser(data.user);
        setVendedor(data.user.nombre || data.user.username);
        showNotification(`¡Bienvenido ${data.user.nombre || data.user.username}!`, 'success');
        loadInventory();
      } else {
        setLoginError(data.message || 'Error al iniciar sesión');
      }
    } catch (error) {
      setLoginError('Error de conexión. Intente nuevamente.');
      console.error('Error en login:', error);
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Cierre de sesión del usuario
  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });

      setIsAuthenticated(false);
      setCurrentUser(null);
      setCart([]);
      setInventory([]);
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    }
  };

  return (
    <>
      {!isAuthenticated ? (
        <LoginScreen
          handleLogin={handleLogin}
          loginForm={loginForm}
          setLoginForm={setLoginForm}
          loginError={loginError}
          isLoggingIn={isLoggingIn} />

      ) : (
        <div className="min-h-screen bg-gray-50">
          {/* Notification Toast */}
          {notification && (
            <div className="fixed top-4 right-4 z-50 animate-slide-in">
              <div className={`rounded-lg shadow-lg p-4 flex items-center gap-3 ${notification.type === 'success'
                ? 'bg-green-700 text-white'
                : 'bg-red-700 text-white'
                }`}>
                {notification.type === 'success' ? (
                  <Check size={24} className="shrink-0" />
                ) : (
                  <X size={24} className="shrink-0" />
                )}
                <p className="font-semibold">{notification.message}</p>
                <button
                  onClick={() => setNotification(null)}
                  className="ml-2 hover:bg-white/20 rounded p-1"
                >
                  <X size={18} />
                </button>
              </div>
            </div>
          )}

          {/* Header */}
          <div className="bg-linear-to-r from-[#008cc8] to-[#005174] text-white p-6 shadow-lg">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold">Comercial TB</h1>
                <p className="text-blue-100 text-sm mt-1">Gestión de Ventas e Inventario</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="bg-white/20 px-3 py-2 rounded-lg">
                  <p className="text-sm">
                    <span className="font-medium">Usuario:</span>{' '}
                    <span className="font-semibold">
                      {currentUser?.nombre || currentUser?.username}
                    </span>
                  </p>
                  <p className="text-xs text-blue-100">
                    {currentUser?.role}
                  </p>
                </div>
                <button
                  onClick={handleLogout}
                  className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition flex items-center gap-2"
                >
                  <X size={20} />
                  Cerrar Sesión
                </button>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white shadow">
            <div className="flex gap-1 px-6 overflow-x-auto">
              <button
                onClick={() => setActiveTab('pos')}
                className={`px-6 py-3 font-semibold transition flex items-center gap-2 whitespace-nowrap ${activeTab === 'pos'
                  ? 'border-b-2 border-[#008cc8] text-[#008cc8]'
                  : 'text-gray-600 hover:text-[#008cc8]'
                  }`}
              >
                <ShoppingCart size={20} />
                Caja
              </button>
              <button
                onClick={() => setActiveTab('inventory-add')}
                className={`px-6 py-3 font-semibold transition flex items-center gap-2 whitespace-nowrap ${activeTab === 'inventory-add'
                  ? 'border-b-2 border-[#008cc8] text-[#008cc8]'
                  : 'text-gray-600 hover:text-[#008cc8]'
                  }`}
              >
                <PackagePlus size={20} />
                Inventario
              </button>
              <button
                onClick={() => {
                  setActiveTab('inventario');
                }}
                className={`px-6 py-3 font-semibold transition flex items-center gap-2 whitespace-nowrap ${activeTab === 'inventario'
                  ? 'border-b-2 border-[#008cc8] text-[#008cc8]'
                  : 'text-gray-600 hover:text-[#008cc8]'
                  }`}
              >
                <Package size={20} />
                Stock
              </button>
              <button
                onClick={() => {
                  setActiveTab('history');
                  loadSalesHistory();
                }}
                className={`px-6 py-3 font-semibold transition flex items-center gap-2 whitespace-nowrap ${activeTab === 'history'
                  ? 'border-b-2 border-[#008cc8] text-[#008cc8]'
                  : 'text-gray-600 hover:text-[#008cc8]'
                  }`}
              >
                <History size={20} />
                Historial de Ventas
              </button>
              <button
                onClick={() => {
                  setActiveTab('profits');
                  loadProfitAnalysis();
                }}
                className={`px-6 py-3 font-semibold transition flex items-center gap-2 whitespace-nowrap ${activeTab === 'profits'
                  ? 'border-b-2 border-[#008cc8] text-[#008cc8]'
                  : 'text-gray-600 hover:text-[#008cc8]'
                  }`}
              >
                <CircleDollarSign size={20} />
                Utilidades
              </button>

            </div>
          </div>

          {/* Alertas */}
          {alerts.length > 0 && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mx-6 mt-4 rounded">
              <div className="flex items-center gap-2">
                <AlertTriangle className="text-yellow-600" />
                <p className="text-yellow-800 font-semibold">
                  {alerts.length} productos con stock bajo
                </p>
              </div>
            </div>
          )}

          {/* Content */}
          <div className="p-6">
            {/* CAJA - Rediseñado */}
            {activeTab === 'pos' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 h-[calc(100vh-210px)]">
                {/* Búsqueda de Productos */}
                <div className="bg-white rounded-lg shadow-lg flex flex-col">
                  <div className="p-4">
                    <h2 className="text-xl font-bold text-gray-800 mb-4">Productos</h2>
                    <div className="relative">
                      <Search className="absolute left-3 top-3 text-gray-400" size={20} />
                      <input
                        type="text"
                        placeholder="Busca por nombre o código..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                      />
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto p-4">
                    {searchTerm.trim() === '' ? (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        <div className="text-center">
                          <Search size={48} className="mx-auto mb-2 opacity-50" />
                          <p>Comienza a escribir para buscar productos</p>
                        </div>
                      </div>
                    ) : filteredInventory.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        <p>No se encontraron productos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {filteredInventory.map(product => (
                          <div
                            key={product.id}
                            onClick={() => addToCart(product)}
                            className={`rounded-lg p-2 transition-all duration-150 
                              ${product.cantidad === 0
                                ? 'bg-gray-100 border-gray-100 cursor-not-allowed'
                                : 'bg-white shadow-sm cursor-pointer hover:-translate-y-1 hover:shadow-md hover:border-[#008cc8]'
                              }`}
                          >
                            <h3 className="font-semibold text-xs text-gray-800 truncate" title={product.nombre}>
                              {product.nombre}
                            </h3>
                            <p className="text-xs text-gray-500 truncate">{product.codigo}</p>
                            <p className="text-sm font-bold text-[#008cc8] mt-1">
                              ${product.precio.toFixed(2)}
                            </p>
                            <p className={`text-xs mt-1 ${product.cantidad === 0 ? 'text-red-600' : 'text-gray-600'
                              }`}>
                              Stock: {product.cantidad}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Carrito de Venta */}
                <div className="bg-white rounded-lg shadow-lg flex flex-col">
                  <div className="p-4">
                    <h2 className="text-xl font-bold text-gray-800">Caja</h2>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    {cart.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        <div className="text-center">
                          <ShoppingCart size={48} className="mx-auto mb-2 opacity-50" />
                          <p>El carrito está vacío</p>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {cart.map(item => (
                          <div key={item.id} className="flex items-center gap-2 bg-gray-100 p-2 rounded-lg">
                            <div className="flex-1 min-w-0">
                              <h3 className="font-semibold text-sm text-gray-800 truncate">{item.nombre}</h3>
                              <p className="text-xs text-gray-500">${item.precio.toFixed(2)} c/u</p>
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => updateCartQuantity(item.id, -1)}
                                className="p-1 text-[#696969] 
                                hover:scale-110
                                active:scale-95"
                              >
                                <Minus size={18} />
                              </button>
                              <span className="w-8 text-center text-sm font-semibold">{item.cantidadVendida}</span>
                              <button
                                onClick={() => updateCartQuantity(item.id, 1)}
                                className="p-1 text-[#696969] 
                                hover:scale-110
                                active:scale-95"
                              >
                                <Plus size={18} />
                              </button>
                            </div>
                            <div className="w-20 text-right">
                              <p className="text-sm font-bold text-gray-800">
                                ${(item.precio * item.cantidadVendida).toFixed(2)}
                              </p>
                            </div>
                            <button
                              onClick={() => removeFromCart(item.id)}
                              className="p-2 text-[#bb1c49] hover:bg-red-50 rounded"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Total y Pago - Ahora siempre visible */}
                  <div className="p-4 space-y-3">
                    <div className="h-px bg-gray-800 mx-auto"></div>
                    <div className="flex justify-between items-center text-2xl font-semibold">
                      <span>Total:</span>
                      <span className="text-[#2b2929]">${calculateTotal().toFixed(2)}</span>
                    </div>

                    {/* Dinero Recibido y Vuelto */}
                    <div className="space-y-2">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Recibe:
                        </label>
                        <div className="relative">
                          <CircleDollarSign className="absolute left-3 top-3 text-gray-400" size={20} />
                          <input
                            type="number"
                            step="0.01"
                            value={receivedMoney}
                            onChange={(e) => setReceivedMoney(e.target.value)}
                            placeholder="0.00"
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                            disabled={cart.length === 0}
                          />
                        </div>
                      </div>

                      {receivedMoney && parseFloat(receivedMoney) >= calculateTotal() && calculateTotal() > 0 && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-green-800">Vuelto:</span>
                            <span className="text-xl font-bold text-green-600">
                              ${calculateChange().toFixed(2)}
                            </span>
                          </div>
                        </div>
                      )}

                      {receivedMoney && parseFloat(receivedMoney) < calculateTotal() && calculateTotal() > 0 && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-red-800">Falta:</span>
                            <span className="text-xl font-bold text-red-600">
                              ${(calculateTotal() - parseFloat(receivedMoney)).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      <button
                        onClick={processSale}
                        disabled={cart.length === 0 || processingSale}
                        className={`px-4 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 
                          ${cart.length === 0 || processingSale
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-[#008cc8] text-white hover:bg-[#007baf]'
                          }`}
                      >
                        {processingSale ? (
                          <>
                            <Loader className="animate-spin" />
                          </>
                        ) : (
                          <>
                            Pagar
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* INVENTARIO - Agregar Productos */}
            {activeTab === 'inventory-add' && (
              <div className="max-w-3xl mx-auto">
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                    Agregar Nuevo Producto
                  </h2>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nombre del Producto <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={newProduct.nombre}
                        onChange={(e) => setNewProduct({ ...newProduct, nombre: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                        placeholder="Ej: Laptop Dell Inspiron"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Costo <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                          <CircleDollarSign className="absolute left-3 top-3 text-gray-400" size={20} />
                          <input
                            type="number"
                            step="0.01"
                            value={newProduct.costo}
                            onChange={(e) => setNewProduct({ ...newProduct, costo: e.target.value })}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                            placeholder="0.00"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          % Ganancia <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={newProduct.porcentajeGanancia}
                          onChange={(e) => setNewProduct({ ...newProduct, porcentajeGanancia: e.target.value })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                          placeholder="Ej: 25"
                        />
                      </div>
                    </div>

                    {/* Vista previa del precio de venta */}
                    {newProduct.costo && newProduct.porcentajeGanancia && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-gray-800">Precio de Venta Calculado:</span>
                          <span className="text-2xl font-bold text-gray-600">
                            ${calculateSalePrice(newProduct.costo, newProduct.porcentajeGanancia)}
                          </span>
                        </div>
                        <p className="text-s text-gray-600 mt-2">
                          Ganancia: ${(calculateSalePrice(newProduct.costo, newProduct.porcentajeGanancia) - parseFloat(newProduct.costo)).toFixed(2)}
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Cantidad Inicial
                        </label>
                        <input
                          type="number"
                          value={newProduct.cantidad}
                          onChange={(e) => setNewProduct({ ...newProduct, cantidad: e.target.value })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                          placeholder="0"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Stock Mínimo
                        </label>
                        <input
                          type="number"
                          value={newProduct.minStock}
                          onChange={(e) => setNewProduct({ ...newProduct, minStock: e.target.value })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                          placeholder="5"
                        />
                      </div>
                    </div>

                    {/* Vista previa del código */}
                    {newProduct.nombre && (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Código que se generará:</p>
                        <p className="text-lg font-mono font-bold text-gray-800 mt-1">
                          {generateProductCode(newProduct.nombre)}
                        </p>
                      </div>
                    )}

                    <div className="flex gap-3 pt-4">
                      <button
                        onClick={() => setNewProduct({
                          nombre: '',
                          costo: '',
                          porcentajeGanancia: '',
                          cantidad: '',
                          minStock: ''
                        })}
                        className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition"
                      >
                        Limpiar
                      </button>
                      <button
                        onClick={addNewProduct}
                        className="flex-1 px-4 py-3 bg-[#008cc8] text-white rounded-lg font-semibold hover:bg-[#057caf] transition flex items-center justify-center gap-2"
                      >
                        <Plus size={20} />
                        Agregar Producto
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STOCK */}
            {activeTab === 'inventario' && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6">
                  <h2 className="text-2xl font-semibold text-gray-800">Inventario de Stock</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {inventory.map(item => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm font-mono text-gray-600">{item.codigo}</td>
                          <td className="px-6 py-4 text-sm text-gray-800">{item.nombre}</td>
                          <td className="px-6 py-4 text-sm">
                            <span className={`font-semibold ${item.cantidad === 0 ? 'text-red-600' :
                              item.cantidad <= item.minStock ? 'text-yellow-600' :
                                'text-green-600'
                              }`}>
                              {item.cantidad}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-800">${item.precio}</td>
                          <td className="px-6 py-4 text-sm">
                            {item.cantidad === 0 ? (
                              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">
                                Sin Stock
                              </span>
                            ) : item.cantidad <= item.minStock ? (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">
                                Stock Bajo
                              </span>
                            ) : (
                              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                                Normal
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* HISTORIAL con filtros */}
            {activeTab === 'history' && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-semibold text-gray-800">Historial de Ventas</h2>
                  </div>

                  {/* Filtros de Fecha */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-gray-50 p-4 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Fecha Inicio:
                      </label>
                      <input
                        type="date"
                        value={filterStartDate}
                        onChange={(e) => setFilterStartDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Fecha Fin:
                      </label>
                      <input
                        type="date"
                        value={filterEndDate}
                        onChange={(e) => setFilterEndDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div className="flex items-end">
                      <button
                        onClick={() => {
                          setFilterStartDate('');
                          setFilterEndDate('');
                        }}
                        className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                      >
                        Limpiar Filtros
                      </button>
                    </div>
                  </div>

                  {/* Información de resultados */}
                  <div className="mt-4 text-sm text-gray-600">
                    Mostrando {filteredSalesHistory.length} de {salesHistory.length} ventas
                  </div>
                </div>

                <div className="overflow-x-auto">
                  {filteredSalesHistory.length === 0 ? (
                    <div className="text-center py-12">
                      <History size={48} className="mx-auto mb-2 text-gray-400" />
                      <p className="text-gray-500">No hay ventas en el rango seleccionado</p>
                    </div>
                  ) : (
                    <table className="w-full">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cantidad</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subtotal</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendedor</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {filteredSalesHistory.map((sale, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm text-gray-600">
                              {new Date(`${sale.Fecha}T${sale.Hora}`).toLocaleString('es-ES')}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-800">{sale.Nombre}</td>
                            <td className="px-6 py-4 text-sm text-gray-600">{sale.Cantidad}</td>
                            <td className="px-6 py-4 text-sm text-gray-600">${sale.PrecioUnitario}</td>
                            <td className="px-6 py-4 text-sm font-semibold text-gray-800">${sale.Subtotal}</td>
                            <td className="px-6 py-4 text-sm font-semibold text-gray-800">${sale.TotalVenta}</td>
                            <td className="px-6 py-4 text-sm text-gray-600">{sale.Vendedor}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}

            {/* Utilidades con filtros */}
            {activeTab === 'profits' && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    Cierre de caja
                  </h2>

                  {/* Selector de Período */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    <button
                      onClick={() => {
                        setSelectedPeriod('today');
                        loadProfitAnalysis('today');
                      }}
                      className={`px-4 py-3 rounded-lg font-semibold transition ${selectedPeriod === 'today'
                        ? 'bg-[#008cc8] text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                    >
                      Hoy
                    </button>
                    <button
                      onClick={() => {
                        setSelectedPeriod('week');
                        loadProfitAnalysis('week');
                      }}
                      className={`px-4 py-3 rounded-lg font-semibold transition ${selectedPeriod === 'week'
                        ? 'bg-[#008cc8] text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                    >
                      Esta Semana
                    </button>
                    <button
                      onClick={() => {
                        setSelectedPeriod('month');
                        loadProfitAnalysis('month');
                      }}
                      className={`px-4 py-3 rounded-lg font-semibold transition ${selectedPeriod === 'month'
                        ? 'bg-[#008cc8] text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                    >
                      Este Mes
                    </button>
                    <button
                      onClick={() => setSelectedPeriod('custom')}
                      className={`px-4 py-3 rounded-lg font-semibold transition ${selectedPeriod === 'custom'
                        ? 'bg-[#008cc8] text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                    >
                      Personalizado
                    </button>
                  </div>

                  {/* Filtro personalizado */}
                  {selectedPeriod === 'custom' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-gray-50 p-4 rounded-lg">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Desde:</label>
                        <input
                          type="date"
                          value={customStartDate}
                          onChange={(e) => setCustomStartDate(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Hasta:</label>
                        <input
                          type="date"
                          value={customEndDate}
                          onChange={(e) => setCustomEndDate(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#008cc8]"
                        />
                      </div>
                      <div className="flex items-end">
                        <button
                          onClick={() => loadProfitAnalysis('custom')}
                          className="w-full px-4 py-2 bg-[#008cc8] text-white rounded-lg hover:bg-[#0176a8] transition"
                        >
                          Consultar
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {profitAnalysis && (
                  <>
                    {/* Encabezado del período */}
                    <div className="bg-linear-to-r from-[#008cc8] to-[#0070a0] text-white p-6 rounded-lg shadow-lg">
                      <h3 className="text-2xl font-bold text-center">{profitAnalysis.periodo}</h3>
                    </div>

                    {/* Tarjetas de Resumen - CIERRE DE CAJA */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 text-sm font-medium">Ingresos</p>
                            <p className="text-2xl font-bold text-blue-600 mt-1">
                              ${profitAnalysis.total_ingresos}
                            </p>
                          </div>
                          <TrendingUp className="text-blue-500" size={32} />
                        </div>
                      </div>

                      <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-red-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 text-sm font-medium">Costos</p>
                            <p className="text-2xl font-bold text-red-600 mt-1">
                              ${profitAnalysis.total_costos}
                            </p>
                          </div>
                          <Minus className="text-red-500" size={32} />
                        </div>
                      </div>

                      <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-green-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 text-sm font-medium">Utilidad Neta</p>
                            <p className="text-2xl font-bold text-green-600 mt-1">
                              ${profitAnalysis.utilidad_neta}
                            </p>
                          </div>
                          <CircleDollarSign className="text-green-500" size={32} />
                        </div>
                      </div>

                      <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-purple-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 text-sm font-medium">Margen</p>
                            <p className="text-2xl font-bold text-purple-600 mt-1">
                              {profitAnalysis.margen_total}%
                            </p>
                          </div>
                          <TrendingUp className="text-purple-500" size={32} />
                        </div>
                      </div>
                    </div>

                    {/* Estadísticas adicionales */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-white p-4 rounded-lg shadow">
                        <p className="text-gray-500 text-sm">Total de Ventas</p>
                        <p className="text-xl font-bold text-gray-800">{profitAnalysis.total_ventas}</p>
                      </div>
                      <div className="bg-white p-4 rounded-lg shadow">
                        <p className="text-gray-500 text-sm">Unidades Vendidas</p>
                        <p className="text-xl font-bold text-gray-800">{profitAnalysis.total_unidades}</p>
                      </div>
                      <div className="bg-white p-4 rounded-lg shadow">
                        <p className="text-gray-500 text-sm">Ticket Promedio</p>
                        <p className="text-xl font-bold text-gray-800">${profitAnalysis.ticket_promedio}</p>
                      </div>
                    </div>

                    {/* Top Productos */}
                    {profitAnalysis.productos_vendidos && profitAnalysis.productos_vendidos.length > 0 && (
                      <div className="bg-white rounded-lg shadow">
                        <div className="p-4">
                          <h3 className="text-lg font-semibold text-gray-800">Top 10 Productos Más Rentables</h3>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="bg-gray-100">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cant.</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ingresos</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Costos</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Utilidad</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {profitAnalysis.productos_vendidos.map((producto, idx) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                  <td className="px-4 py-3 text-sm text-gray-800">{producto.producto}</td>
                                  <td className="px-4 py-3 text-sm text-right text-gray-600">{producto.cantidad}</td>
                                  <td className="px-4 py-3 text-sm text-right text-blue-600">
                                    ${producto.ingresos}
                                  </td>
                                  <td className="px-4 py-3 text-sm text-right text-red-600">
                                    ${producto.costos}
                                  </td>
                                  <td className="px-4 py-3 text-sm text-right font-semibold text-green-600">
                                    ${producto.utilidad}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Estadísticas por Vendedor */}
                    {profitAnalysis.vendedores && profitAnalysis.vendedores.length > 0 && (
                      <div className="bg-white rounded-lg shadow">
                        <div className="p-4">
                          <h3 className="text-lg font-semibold text-gray-800">Rendimiento por Vendedor</h3>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="bg-gray-100">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendedor</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ventas</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ingresos</th>
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Utilidad</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {profitAnalysis.vendedores.map((vendedor, idx) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                  <td className="px-4 py-3 text-sm text-gray-800 font-medium">{vendedor.vendedor}</td>
                                  <td className="px-4 py-3 text-sm text-right text-gray-600">{vendedor.ventas}</td>
                                  <td className="px-4 py-3 text-sm text-right text-blue-600">
                                    ${vendedor.ingresos}
                                  </td>
                                  <td className="px-4 py-3 text-sm text-right font-semibold text-green-600">
                                    ${vendedor.utilidad}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default POSSystem;