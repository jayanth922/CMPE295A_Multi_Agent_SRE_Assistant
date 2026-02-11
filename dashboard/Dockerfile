# Base image
FROM node:18-alpine

WORKDIR /app

# Install dependencies (cache layer)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build for production? Or explicit dev mode for now?
# User asked for "scaffolding". Dev mode is better for now.
# CMD ["npm", "run", "dev"]

# Exposed port
EXPOSE 3000

CMD ["npm", "run", "dev"]
