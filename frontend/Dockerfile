FROM node:20-alpine

WORKDIR /app

# Install dependencies in a separate layer so they cache between code changes.
COPY package.json package-lock.json* ./
RUN npm install

# Bring in the rest of the source.
# The volumes in docker-compose.yml will overlay this with your live local files.
COPY . .

EXPOSE 3000

# Dev server with hot reload. Listens on all interfaces so the host can reach it.
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
