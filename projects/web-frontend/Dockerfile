FROM node:20-slim
WORKDIR /frontend
COPY package.json .
COPY package-lock.json .
COPY . .
RUN npm install
CMD ["npm", "run", "dev"]
EXPOSE 1324
