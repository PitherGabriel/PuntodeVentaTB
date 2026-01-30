# Frontend Dockerfile - DESARROLLO
FROM node:20-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Exponer puerto de desarrollo
EXPOSE 5173

# Comando para desarrollo con hot-reload
CMD ["npm", "run", "dev"]