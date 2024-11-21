# Step 1: Build the image using the official Node.js base image
FROM node:21-alpine as builder

RUN apk add --no-cache git

ARG SYS_KEY
ENV SYS_KEY=$SYS_KEY

ARG NEXT_PUBLIC_PROJECT_ID
ENV NEXT_PUBLIC_PROJECT_ID=$NEXT_PUBLIC_PROJECT_ID

ARG NEXT_PUBLIC_TELEGRAM_APP_URL
ENV NEXT_PUBLIC_TELEGRAM_APP_URL=$NEXT_PUBLIC_TELEGRAM_APP_URL

ARG NEXT_PUBLIC_API_HOST
ENV NEXT_PUBLIC_API_HOST=$NEXT_PUBLIC_API_HOST

ARG AUTH_SECRET
ENV AUTH_SECRET=$AUTH_SECRET

ARG NEXT_PUBLIC_GA_TRACKING_ID
ENV NEXT_PUBLIC_GA_TRACKING_ID=$NEXT_PUBLIC_GA_TRACKING_ID

ARG NEXT_PUBLIC_YANDEX_METRICA_ID
ENV NEXT_PUBLIC_YANDEX_METRICA_ID=$NEXT_PUBLIC_YANDEX_METRICA_ID


ARG NEXT_PUBLIC_APP_INTRO
ENV NEXT_PUBLIC_APP_INTRO=$NEXT_PUBLIC_APP_INTRO
ARG NEXT_PUBLIC_APP_CURRENCY
ENV NEXT_PUBLIC_APP_CURRENCY=$NEXT_PUBLIC_APP_CURRENCY
ARG NEXT_PUBLIC_APP_NAME
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
ARG NEXT_PUBLIC_APP_CHAIN_ID
ENV NEXT_PUBLIC_APP_CHAIN_ID=$NEXT_PUBLIC_APP_CHAIN_ID
ARG NEXT_PUBLIC_APP_RPC_URL
ENV NEXT_PUBLIC_APP_RPC_URL=$NEXT_PUBLIC_APP_RPC_URL
ARG NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS
ENV NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS=$NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS
ARG NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL
ENV NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL=$NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL
ARG NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME
ENV NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME=$NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME
ARG NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL
ENV NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL=$NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL
ARG NEXT_PUBLIC_APP_CHAIN_LABEL
ENV NEXT_PUBLIC_APP_CHAIN_LABEL=$NEXT_PUBLIC_APP_CHAIN_LABEL

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json (or yarn.lock) files into the working directory
COPY package.json ./
COPY yarn.lock ./
COPY next.config.mjs ./

# Install dependencies
RUN yarn install

# Copy the rest of your application's source code into the working directory
COPY . .

# Build your Next.js application
RUN yarn build

# Step 2: Run the built application using a lightweight Node.js image
FROM node:21-alpine

WORKDIR /app

COPY package.json ./
COPY yarn.lock ./

# Copy the built application from the previous stage
# Uncomment or add the next.config.js file copy command if necessary and present
# COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.mjs ./

# Expose the port your app runs on
EXPOSE 3000

# Command to run your app
CMD ["yarn", "start"]
