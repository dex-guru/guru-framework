# Use the official Node.js image from the Docker Hub
FROM node:20

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install curl
RUN apt-get update && apt-get install -y curl

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh

# Install the application's dependencies
RUN npm update

# Copy the application code
COPY . .

# Set the environment variable
ENV PATH="/root/.deno/bin:$PATH"


# Expose the port the app runs on
EXPOSE 3000

# Command to run the application
CMD ["node", "request.mjs"]
