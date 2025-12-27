FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3003

# Run the application
CMD ["node", "server.js"]

