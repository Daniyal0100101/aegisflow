FROM node:18-alpine

WORKDIR /app

# Copy dependency manifest
COPY apps/web/package.json ./package.json
RUN npm install

# Copy application files
COPY apps/web/ ./

# Disable Next.js telemetry and compile production distribution
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
