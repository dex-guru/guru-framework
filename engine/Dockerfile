# Step 1: Build the application in a Maven container with Corretto 11
FROM maven:3.8.3-jdk-11-slim AS build

# Set the working directory in the Docker container
WORKDIR /app

# Copy the Maven pom.xml and source code to the container
COPY pom.xml .
COPY src ./src/

# Build the application
RUN mvn clean package

# Step 2: Use Amazon Corretto 11 base image to run the application
FROM amazoncorretto:11

# Set the working directory in the Docker container
WORKDIR /app

# Copy the built application from the Maven container to the Corretto 11 container
COPY --from=build /app/target/chainflow-engine.jar /app/

# Set the entry point to run the application
ENTRYPOINT ["java", "-jar", "chainflow-engine.jar"]
