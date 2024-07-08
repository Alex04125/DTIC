# Use a multi-stage build to minimize the final image size
FROM node:14.17.0 as build

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json to the working directory
COPY package*.json ./

# Install the dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the React application
RUN npm run build

# Use Nginx to serve the static files
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80 to access the application
EXPOSE 80

# Command to start Nginx
CMD ["nginx", "-g", "daemon off;"]
